import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import database
from models.switch import Switch
from models.cdp_neighbor import CdpNeighbor, CdpNeighborHistory


def setup():
    """テスト前にCDP関連テーブルをクリア（switches は残す）"""
    session = database.connect_db()
    session.query(CdpNeighborHistory).delete()
    session.query(CdpNeighbor).delete()
    session.query(Switch).delete()
    session.commit()
    session.close()


def print_json(label, data):
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def test_topology():
    # スイッチ登録
    # test_cdp_neighbor.py の Switch.get_or_create部分を修正
    core = Switch.get_or_create(
        hostname="core-sw01", ip_address="192.168.1.1",
        hardware_model="C3850", switch_type="L3", role="core",
        base_mac_address="aa:bb:cc:00:00:01",
    )
    sw01 = Switch.get_or_create(
        hostname="edge-sw01", ip_address="192.168.10.21",  # .11 → .21 に変更
        hardware_model="C2960L", switch_type="L2", role="edge",
        base_mac_address="aa:bb:cc:00:00:02",
    )
    sw02 = Switch.get_or_create(
        hostname="edge-sw02", ip_address="192.168.10.22",  # .12 → .22 に変更
        hardware_model="C2960L", switch_type="L2", role="edge",
        base_mac_address="aa:bb:cc:00:00:03",
    )

    # core-sw01 側から見た隣接情報
    CdpNeighbor.sync_from_collection(core.id, [
        {
            "local_interface": "Gi1/0/1", "neighbor_hostname_raw": "edge-sw01",
            "neighbor_interface": "Gi0/1", "neighbor_platform": "cisco WS-C2960L",
            "neighbor_chassis_mac": "aa:bb:cc:00:00:02",
        },
        {
            "local_interface": "Gi1/0/2", "neighbor_hostname_raw": "edge-sw02",
            "neighbor_interface": "Gi0/1", "neighbor_platform": "cisco WS-C2960L",
            "neighbor_chassis_mac": "aa:bb:cc:00:00:03",
        },
    ])

    # edge-sw01 側から見た隣接情報（逆方向 + 未解決のIP電話も含む）
    CdpNeighbor.sync_from_collection(sw01.id, [
        {
            "local_interface": "Gi0/1", "neighbor_hostname_raw": "core-sw01",
            "neighbor_interface": "Gi1/0/1", "neighbor_platform": "cisco WS-C3850",
            "neighbor_chassis_mac": "aa:bb:cc:00:00:01",
        },
        {
            "local_interface": "Gi0/10", "neighbor_hostname_raw": "SEP001122334455",  # IP電話
            "neighbor_interface": None, "neighbor_platform": "Cisco IP Phone",
            "neighbor_chassis_mac": None,
        },
    ])

    # edge-sw02 側から見た隣接情報
    CdpNeighbor.sync_from_collection(sw02.id, [
        {
            "local_interface": "Gi0/1", "neighbor_hostname_raw": "core-sw01",
            "neighbor_interface": "Gi1/0/2", "neighbor_platform": "cisco WS-C3850",
            "neighbor_chassis_mac": "aa:bb:cc:00:00:01",
        },
    ])

    print_json("ノード一覧", CdpNeighbor.fetch_topology_nodes())
    print_json("エッジ一覧(重複排除済み)", CdpNeighbor.fetch_topology_edges())


if __name__ == "__main__":
    test_topology()