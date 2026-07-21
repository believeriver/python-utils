import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.switch import Switch
from models.arp_entry import ArpEntry, ArpHistory


def print_json(label, data):
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def setup():
    from models.db import database
    session = database.connect_db()
    session.query(ArpHistory).delete()
    session.query(ArpEntry).delete()
    session.commit()
    session.close()


def test_arp_sync():
    setup()

    core = Switch.get_or_create(
        hostname="core-sw01", ip_address="192.168.1.1",
        hardware_model="C3850", switch_type="L3", role="core",
    )

    # 1回目の収集
    ArpEntry.sync_from_collection(core.id, [
        {"vlan": 10, "ip_address": "10.1.10.1", "mac_address": "aa:bb:cc:dd:ee:01"},
        {"vlan": 10, "ip_address": "10.1.10.2", "mac_address": "aa:bb:cc:dd:ee:02"},
    ])
    print_json("1回目収集後: 10.1.10.1", ArpEntry.fetch_by_ip("10.1.10.1"))

    # 2回目の収集：10.1.10.1のMACが変わり、10.1.10.2が消えた
    ArpEntry.sync_from_collection(core.id, [
        {"vlan": 10, "ip_address": "10.1.10.1", "mac_address": "aa:bb:cc:dd:ee:99"},
    ])

    result = {
        "current": ArpEntry.fetch_by_ip("10.1.10.1"),
        "history": ArpHistory.fetch_by_ip("10.1.10.1"),
    }
    print_json("2回目収集後: 10.1.10.1 (MAC変化)", result)

    result_disappeared = {
        "current": ArpEntry.fetch_by_ip("10.1.10.2"),   # Noneになるはず
        "history": ArpHistory.fetch_by_ip("10.1.10.2"),
    }
    print_json("2回目収集後: 10.1.10.2 (消失分)", result_disappeared)


if __name__ == "__main__":
    test_arp_sync()