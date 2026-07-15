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
    """C1300系。ページング無効化コマンドが異なる想定、出力形式も要検証"""
    PRE_COMMANDS = ["terminal logging"]
    SUPPORTS_ARP = False


# hardware_model文字列(show versionのModel numberの値)は、
# 実機で確認でき次第、随時この対応表に追加してください
DEVICE_PROFILE_MAP = {
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

DEFAULT_PROFILE = LegacyIOSProfile  # 未登録機種は安全側(ARP非対応)として扱う


def get_profile(hardware_model: str) -> type:
    return DEVICE_PROFILE_MAP.get(hardware_model, DEFAULT_PROFILE)
