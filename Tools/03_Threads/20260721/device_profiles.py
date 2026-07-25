"""
スイッチの機種(ハードウェアモデル)ごとに異なるCLIコマンド・パース方法を管理するモジュール。
Switch.hardware_model(CSVまたはshow versionから取得した値)を元に、
実行すべき前処理コマンド・showコマンド・パーサー関数を切り替える。
"""

import parsers.parse as parse_module


class DeviceProfile:
    """機種ファミリーごとのコマンド差分を定義する基底クラス(IOS系のデフォルト)"""
    PRE_COMMANDS: list = ["terminal length 0"]
    SUPPORTS_ARP: bool = True
    MAC_TABLE_CMD: str = "show mac address-table"
    CDP_CMD: str = "show cdp neighbors detail"
    ARP_CMD: str = "show ip arp"
    INVENTORY_CMDS: list = ["show version", "show inventory"]
    # パーサーを差し替えたい機種だけ、以下の属性をサブクラスで上書きする
    # (未指定の場合は parsers/parse.py の既定関数が使われる)
    VERSION_PARSER: str = None
    INVENTORY_PARSER: str = None
    MAC_TABLE_PARSER: str = None
    CDP_PARSER: str = None
    ARP_PARSER: str = None


class LegacyIOSProfile(DeviceProfile):
    """C1000 / C2960L系。L2アクセス、ARP非対応"""
    PRE_COMMANDS = ["terminal length 0"]
    SUPPORTS_ARP = False


class Catalyst9KFloorProfile(DeviceProfile):
    """C9200 / C9300系。フロアスイッチ、ARP非対応(L2運用想定)"""
    PRE_COMMANDS = ["terminal length 0"]
    SUPPORTS_ARP = False


class Catalyst9KCoreProfile(DeviceProfile):
    """C9500系。コア、L3、ARP対応"""
    PRE_COMMANDS = ["terminal length 0"]
    SUPPORTS_ARP = True


class C1300Profile(DeviceProfile):
    # """C1300系。Cisco Small Business系CLI。IOS系とは出力形式が大きく異なる"""
    # PRE_COMMANDS = ["terminal datadump"]
    # SUPPORTS_ARP = True
    # ARP_CMD = "show arp"                                     # show ip arp ではない
    # VERSION_PARSER = "parse_show_version_smb"
    # INVENTORY_PARSER = "parse_show_inventory_smb"
    # MAC_TABLE_PARSER = "parse_mac_address_table_c1300"
    # CDP_PARSER = "parse_cdp_neighbors_detail_c1300"
    # ARP_PARSER = "parse_arp_table_c1300"
    """C1300系。Cisco Small Business系CLI。IOS系とは出力形式が大きく異なる"""
    PRE_COMMANDS = ["terminal datadump"]
    SUPPORTS_ARP = True
    ARP_CMD = "show arp"
    VERSION_PARSER = "parse_show_version_smb"  # ← show versionは引き続きSMB用が必要か確認
    INVENTORY_PARSER = None  # ← 未指定にして、既定(IOS用)にフォールバックさせる
    MAC_TABLE_PARSER = "parse_mac_address_table_c1300"
    CDP_PARSER = "parse_cdp_neighbors_detail_c1300"
    ARP_PARSER = "parse_arp_table_c1300"


# ---------------------------------------------------------------------------
# 機種名 → プロファイルの対応表
# ---------------------------------------------------------------------------

# 完全一致(特定の1機種だけ挙動を変えたい例外ケース用。通常は空でよい)
DEVICE_PROFILE_MAP_EXACT = {
    "WS-C3850-24T": Catalyst9KCoreProfile,   # テスト機のコアスイッチ
}

# プレフィックス一致(型番の先頭で判定。ポート数・PoE有無の違いを吸収)
DEVICE_PROFILE_MAP_PREFIX = [
    ("C1000", LegacyIOSProfile),
    ("WS-C2960L", LegacyIOSProfile),
    ("C1300", C1300Profile),
    ("C9200", Catalyst9KFloorProfile),
    ("C9300", Catalyst9KFloorProfile),
    ("C9500", Catalyst9KCoreProfile),
    ("WS-C3850", Catalyst9KCoreProfile),
]

DEFAULT_PROFILE = LegacyIOSProfile  # 未登録機種は安全側(ARP非対応)として扱う


def get_profile(hardware_model: str):
    """
    hardware_model文字列からプロファイルクラスを決定する。
    1. 完全一致 → 2. プレフィックス一致 → 3. デフォルト、の優先順位。
    """
    if hardware_model in DEVICE_PROFILE_MAP_EXACT:
        return DEVICE_PROFILE_MAP_EXACT[hardware_model]

    for prefix, profile in DEVICE_PROFILE_MAP_PREFIX:
        if hardware_model.startswith(prefix):
            return profile

    return DEFAULT_PROFILE


def get_parser(hardware_model: str, parser_attr: str, default_fn):
    """
    機種プロファイルに応じたパーサー関数を返す汎用ヘルパー。
    parser_attr: "VERSION_PARSER" / "INVENTORY_PARSER" / "MAC_TABLE_PARSER" /
                 "CDP_PARSER" / "ARP_PARSER" のいずれか
    default_fn:  該当プロファイルに専用パーサーの指定が無い場合に使う既定関数(IOS系)
    """
    profile = get_profile(hardware_model)
    parser_name = getattr(profile, parser_attr, None)
    if parser_name:
        return getattr(parse_module, parser_name)
    return default_fn
