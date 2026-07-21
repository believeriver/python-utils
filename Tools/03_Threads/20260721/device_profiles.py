class DeviceProfile:
    """機種ファミリーごとのコマンド差分を定義する基底クラス"""
    PRE_COMMANDS: list = ["terminal length 0"]
    SUPPORTS_ARP: bool = True
    MAC_TABLE_CMD: str = "show mac address-table"
    CDP_CMD: str = "show cdp neighbors detail"
    ARP_CMD: str = "show ip arp"
    INVENTORY_CMDS: list = ["show version", "show inventory"]


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
    """C1300系。Cisco Small Business系CLI。IOS系とは出力形式が大きく異なる"""
    PRE_COMMANDS = ["terminal datadump"]  # "terminal logging"は誤り、正しくはこちら
    SUPPORTS_ARP = True                    # ARP自体は"show arp"で取得可能(L3機能次第)
    ARP_CMD = "show arp"                   # show ip arp ではない
    MAC_TABLE_PARSER = "parse_mac_address_table_c1300"  # 専用パーサーを使う目印
    CDP_PARSER = "parse_cdp_neighbors_detail_c1300"


# hardware_model文字列(show versionのModel numberの値)は、
# 実機で確認でき次第、随時この対応表に追加してください
DEVICE_PROFILE_MAP_EXACT = {
    # C1000シリーズ
    "C1000-8T": LegacyIOSProfile,
    "C1000-24T": LegacyIOSProfile,
    # C2960Lシリーズ(既存)
    "WS-C2960L-8TS-LL": LegacyIOSProfile,
    # C9200/C9300(フロア)
    "C9200-24P": Catalyst9KFloorProfile,
    "C9300-24T": Catalyst9KFloorProfile,
    # C9500(コア)
    "C9500-24Y4C": Catalyst9KCoreProfile,
    "WS-C3850-24T": Catalyst9KCoreProfile,   # 追加：テスト機のコアスイッチ
    # C1300シリーズ(要検証)
    "C1300-8T": C1300Profile,
}

# プレフィックス一致用(型番の先頭で判定、ポート数・PoE有無の違いを吸収)
DEVICE_PROFILE_MAP_PREFIX = [
    ("C1000", LegacyIOSProfile),
    ("WS-C2960L", LegacyIOSProfile),
    ("C1300", C1300Profile),
    ("C9200", Catalyst9KFloorProfile),
    ("C9300", Catalyst9KFloorProfile),
    ("C9500", Catalyst9KCoreProfile),
    ("WS-C3850", Catalyst9KCoreProfile),  # テスト環境のコアスイッチ用
]

DEFAULT_PROFILE = LegacyIOSProfile  # 未登録機種は安全側(ARP非対応)として扱う


# def get_profile(hardware_model: str) -> type:
#     return DEVICE_PROFILE_MAP.get(hardware_model, DEFAULT_PROFILE)
def get_profile(hardware_model: str) -> type:
    # 1. 完全一致を優先(特殊な例外モデルがあれば、ここで個別対応できる)
    if hardware_model in DEVICE_PROFILE_MAP_EXACT:
        return DEVICE_PROFILE_MAP_EXACT[hardware_model]

    # 2. プレフィックス一致(ポート数・PoE違いを吸収)
    for prefix, profile in DEVICE_PROFILE_MAP_PREFIX:
        if hardware_model.startswith(prefix):
            return profile

    # 3. どちらにも該当しなければ安全側のデフォルト
    return DEFAULT_PROFILE

import parsers.parse as parse_module


def get_mac_table_parser(hardware_model: str):
    """機種に応じたMACアドレステーブル用パーサー関数を返す"""
    profile = get_profile(hardware_model)
    parser_name = getattr(profile, "MAC_TABLE_PARSER", None)
    if parser_name:
        return getattr(parse_module, parser_name)
    return parse_module.parse_mac_address_table  # 既定(IOS系)


def get_cdp_parser(hardware_model: str):
    """機種に応じたCDPネイバー用パーサー関数を返す"""
    profile = get_profile(hardware_model)
    parser_name = getattr(profile, "CDP_PARSER", None)
    if parser_name:
        return getattr(parse_module, parser_name)
    return parse_module.parse_cdp_neighbors_detail  # 既定(IOS系)


def get_arp_parser(hardware_model: str):
    """機種に応じたARP用パーサー関数を返す"""
    profile = get_profile(hardware_model)
    parser_name = getattr(profile, "ARP_PARSER", None)
    if parser_name:
        return getattr(parse_module, parser_name)
    return parse_module.parse_arp_table  # 既定(IOS系)

