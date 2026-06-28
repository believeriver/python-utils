import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.switch import Switch
from models.mac_address import MacAddressEntry, MacAddressHistory


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
    print("1回目:", MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:01"))

    # 2回目の収集：1件目がポート移動、2件目が消失
    MacAddressEntry.sync_from_collection(switch.id, [
        {"vlan": 10, "mac_address": "aa:bb:cc:dd:ee:01", "port": "Gi1/0/5"},
    ])

    print("2回目(現在):", MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:01"))
    print("1件目の履歴:", MacAddressHistory.fetch_by_mac("aa:bb:cc:dd:ee:01"))
    print("2件目の履歴(消失分):", MacAddressHistory.fetch_by_mac("aa:bb:cc:dd:ee:02"))
    print("2件目の現在(Noneになるはず):", MacAddressEntry.fetch_by_mac("aa:bb:cc:dd:ee:02"))


if __name__ == "__main__":
    test_sync_and_history()