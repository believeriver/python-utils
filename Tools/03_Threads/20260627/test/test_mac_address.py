import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.switch import Switch
from models.mac_address import MacAddressEntry, MacAddressHistory


def print_json(label: str, data) -> None:
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def test_sync_and_history():
    switch = Switch.get_or_create(
        hostname="sw-3f-edge-01", ip_address="192.168.10.11",
        hardware_model="C2960L", switch_type="L2", role="edge",
    )

    # 1回目の収集：2件のMACが見える
    MacAddressEntry.sync_from_collection(switch.id, [
        {"vlan": 10, "mac_address": "aa:bb:cc:dd:ee:01", "port": "Gi1/0/1"},
        {"vlan": 10, "mac_address": "aa:bb:cc:dd:ee:02", "port": "Gi1/0/2"},
    ])
    print_json("1回目収集後: aa:bb:cc:dd:ee:01", MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:01"))

    # 2回目の収集：1件目がポート移動、2件目が消失
    MacAddressEntry.sync_from_collection(switch.id, [
        {"vlan": 10, "mac_address": "aa:bb:cc:dd:ee:01", "port": "Gi1/0/5"},
    ])

    result = {
        "current": MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:01"),
        "history": MacAddressHistory.fetch_by_mac("aa:bb:cc:dd:ee:01"),
    }
    print_json("2回目収集後: aa:bb:cc:dd:ee:01 (現在+履歴)", result)

    result_disappeared = {
        "current": MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:02"),  # Noneになるはず
        "history": MacAddressHistory.fetch_by_mac("aa:bb:cc:dd:ee:02"),
    }
    print_json("2回目収集後: aa:bb:cc:dd:ee:02 (消失分)", result_disappeared)


if __name__ == "__main__":
    test_sync_and_history()