import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.switch import Switch
from models.cdp_neighbor import CdpNeighbor


def print_json(label, data):
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def test_sync_topology():
    sw1 = Switch.get_or_create(
        hostname="sw-3f-edge-01", ip_address="192.168.10.11",
        hardware_model="C2960L", switch_type="L2", role="edge",
        base_mac_address="aa:bb:cc:dd:ee:01",
    )
    sw2 = Switch.get_or_create(
        hostname="sw-3f-edge-02", ip_address="192.168.10.12",
        hardware_model="C2960L", switch_type="L2", role="edge",
        base_mac_address="aa:bb:cc:dd:ee:02",
    )

    # chassis_macで名前解決できるケース
    CdpNeighbor.sync_from_collection(sw1.id, [
        {
            "local_interface": "Gi1/0/24",
            "neighbor_hostname_raw": "sw-3f-edge-02.example.local",
            "neighbor_interface": "Gi0/1",
            "neighbor_platform": "cisco WS-C2960L",
            "neighbor_chassis_mac": "aa:bb:cc:dd:ee:02",
        },
    ])

    print_json("トポロジー一覧", CdpNeighbor.fetch_topology())


if __name__ == "__main__":
    test_sync_topology()