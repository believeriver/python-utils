import sys
import os
import datetime
from typing import List, Optional, Dict

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, setup_logger
from models.db import BaseDatabase, database
from models.switch import Switch

logger = setup_logger("CdpNeighbor", Config.LEVEL)


class CdpNeighbor(BaseDatabase):
    """現在の状態：(switch, local_interface)につき1行のみ"""
    __tablename__ = "cdp_neighbors"
    __table_args__ = (
        UniqueConstraint("switch_id", "local_interface", name="uq_switch_local_interface"),
    )

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    local_interface = Column(String(32), nullable=False)

    neighbor_hostname_raw = Column(String(128), nullable=False)
    neighbor_interface = Column(String(32), nullable=True)
    neighbor_platform = Column(String(64), nullable=True)
    neighbor_chassis_mac = Column(String(17), nullable=True)

    resolved_switch_id = Column(Integer, ForeignKey("switches.id"), nullable=True)

    switch = relationship("Switch", foreign_keys=[switch_id])
    resolved_switch = relationship("Switch", foreign_keys=[resolved_switch_id])

    @staticmethod
    def _resolve_neighbor_switch_id(session, chassis_mac: Optional[str], hostname_raw: str) -> Optional[int]:
        """隣接機器をインベントリ上のSwitchに名前解決する。chassis_mac優先、なければホスト名で照合"""
        if chassis_mac:
            row = session.query(Switch).filter(Switch.base_mac_address == chassis_mac).first()
            if row:
                return row.id

        normalized = hostname_raw.split(".")[0].lower()  # ドメインサフィックス・大文字小文字のブレを吸収
        for candidate in session.query(Switch).all():
            if candidate.hostname.split(".")[0].lower() == normalized:
                return candidate.id
        return None

    @staticmethod
    def sync_from_collection(switch_id: int, collected_neighbors: List[Dict]) -> None:
        """
        1スイッチ分のshow cdp neighbor detail結果をまとめて反映する。
        collected_neighbors: [{
            "local_interface": "Gi1/0/24",
            "neighbor_hostname_raw": "sw-3f-edge-02.example.local",
            "neighbor_interface": "Gi0/1",
            "neighbor_platform": "cisco WS-C2960L",
            "neighbor_chassis_mac": "aa:bb:cc:dd:ee:ff",
        }, ...]
        """
        session = database.connect_db()
        now = datetime.datetime.utcnow()

        existing_rows = session.query(CdpNeighbor).filter(
            CdpNeighbor.switch_id == switch_id
        ).all()
        existing_map = {row.local_interface: row for row in existing_rows}
        seen_ports = set()

        for entry in collected_neighbors:
            local_if = entry["local_interface"]
            seen_ports.add(local_if)
            row = existing_map.get(local_if)

            resolved_id = CdpNeighbor._resolve_neighbor_switch_id(
                session, entry.get("neighbor_chassis_mac"), entry["neighbor_hostname_raw"]
            )

            unchanged = (
                row is not None
                and row.neighbor_hostname_raw == entry["neighbor_hostname_raw"]
                and row.neighbor_interface == entry.get("neighbor_interface")
                and row.neighbor_chassis_mac == entry.get("neighbor_chassis_mac")
            )

            if row is None:
                session.add(CdpNeighbor(
                    switch_id=switch_id, local_interface=local_if,
                    neighbor_hostname_raw=entry["neighbor_hostname_raw"],
                    neighbor_interface=entry.get("neighbor_interface"),
                    neighbor_platform=entry.get("neighbor_platform"),
                    neighbor_chassis_mac=entry.get("neighbor_chassis_mac"),
                    resolved_switch_id=resolved_id,
                ))
                logger.info(f"new neighbor: {local_if} -> {entry['neighbor_hostname_raw']}")

            elif unchanged:
                row.updated_at = now

            else:
                session.add(CdpNeighborHistory(
                    switch_id=row.switch_id, local_interface=row.local_interface,
                    neighbor_hostname_raw=row.neighbor_hostname_raw,
                    neighbor_interface=row.neighbor_interface,
                    valid_from=row.created_at, valid_to=now,
                ))
                logger.info(
                    f"neighbor changed: {local_if} {row.neighbor_hostname_raw} -> {entry['neighbor_hostname_raw']}"
                )
                row.neighbor_hostname_raw = entry["neighbor_hostname_raw"]
                row.neighbor_interface = entry.get("neighbor_interface")
                row.neighbor_platform = entry.get("neighbor_platform")
                row.neighbor_chassis_mac = entry.get("neighbor_chassis_mac")
                row.resolved_switch_id = resolved_id
                row.created_at = now
                row.updated_at = now

        # 今回出てこなかったポート = ケーブル抜け・撤去等とみなしてhistory化
        for local_if, row in existing_map.items():
            if local_if not in seen_ports:
                session.add(CdpNeighborHistory(
                    switch_id=row.switch_id, local_interface=row.local_interface,
                    neighbor_hostname_raw=row.neighbor_hostname_raw,
                    neighbor_interface=row.neighbor_interface,
                    valid_from=row.created_at, valid_to=now,
                ))
                logger.info(f"neighbor disappeared: {local_if} (was {row.neighbor_hostname_raw})")
                session.delete(row)

        session.commit()
        session.close()

    @staticmethod
    def fetch_topology() -> List[dict]:
        """全スイッチの隣接関係一覧(トポロジー表示用)"""
        session = database.connect_db()
        rows = session.query(CdpNeighbor).all()
        result = [{
            "switch_hostname": row.switch.hostname,
            "local_interface": row.local_interface,
            "neighbor_hostname_raw": row.neighbor_hostname_raw,
            "neighbor_interface": row.neighbor_interface,
            "resolved_hostname": row.resolved_switch.hostname if row.resolved_switch else None,
            "last_seen": row.updated_at,
        } for row in rows]
        session.close()
        return result

    @staticmethod
    def fetch_topology_edges() -> list:
        """
        トポロジー描画用に、双方向リンクの重複を排除した辺リストを返す。

        戻り値の例:
        [
            {
                "switch_a": "core-sw01",
                "port_a": "Gi1/0/1",
                "switch_b": "edge-sw01",
                "port_b": "Gi0/1",
                "resolved": True,
                "confirmed_both_sides": True,
            },
            ...
        ]
        """
        session = database.connect_db()
        rows = session.query(CdpNeighbor).all()

        edges = {}
        for row in rows:
            sw_a = row.switch.hostname
            sw_b = row.resolved_switch.hostname if row.resolved_switch else row.neighbor_hostname_raw

            key = frozenset([sw_a, sw_b])

            if key not in edges:
                edges[key] = {
                    "switch_a": sw_a,
                    "port_a": row.local_interface,
                    "switch_b": sw_b,
                    "port_b": row.neighbor_interface,
                    "resolved": row.resolved_switch is not None,
                    "confirmed_both_sides": False,
                }
            else:
                edges[key]["confirmed_both_sides"] = True

        session.close()
        return list(edges.values())

    @staticmethod
    def fetch_topology_nodes() -> list:
        """
        トポロジー描画用ノードリストを返す。
        インベントリに登録済みのスイッチ + 未解決の隣接機器(IP電話・AP等)を含む。
        """
        session = database.connect_db()
        rows = session.query(CdpNeighbor).all()

        # インベントリ登録済みノード
        known = {row.switch.hostname for row in rows}
        known |= {row.resolved_switch.hostname for row in rows if row.resolved_switch}

        # 未解決ノード(resolved_switch_idがNullのもの)
        unknown = {row.neighbor_hostname_raw for row in rows if row.resolved_switch is None}

        session.close()

        nodes = [{"hostname": h, "resolved": True} for h in known]
        nodes += [{"hostname": h, "resolved": False} for h in unknown]
        return nodes

    # models/cdp_neighbor.py に追加

    @staticmethod
    def fetch_topology_subgraph(center_hostname: str, max_hops: int = 2) -> dict:
        """
        指定したホストを起点に、max_hops先までの部分トポロジーを返す。
        戻り値: {"nodes": [...], "edges": [...]}  (fetch_topology_nodes/edgesと同じ形式)
        """
        all_edges = CdpNeighbor.fetch_topology_edges()

        # 隣接リストを構築(スイッチ名 -> [(隣接スイッチ名, エッジ情報), ...])
        adjacency = {}
        for e in all_edges:
            adjacency.setdefault(e["switch_a"], []).append((e["switch_b"], e))
            adjacency.setdefault(e["switch_b"], []).append((e["switch_a"], e))

        if center_hostname not in adjacency:
            return {"nodes": [], "edges": []}

        # BFSでmax_hops先までのノードを探索
        visited = {center_hostname: 0}  # hostname -> hop数
        queue = [center_hostname]
        included_edges = []

        while queue:
            current = queue.pop(0)
            current_hop = visited[current]
            if current_hop >= max_hops:
                continue

            for neighbor, edge in adjacency.get(current, []):
                if edge not in included_edges:
                    included_edges.append(edge)
                if neighbor not in visited:
                    visited[neighbor] = current_hop + 1
                    queue.append(neighbor)

        # ノード情報を構築(resolvedかどうかの判定に既存データを流用)
        all_nodes = {n["hostname"]: n for n in CdpNeighbor.fetch_topology_nodes()}
        result_nodes = [all_nodes[h] for h in visited if h in all_nodes]

        return {"nodes": result_nodes, "edges": included_edges}


class CdpNeighborHistory(BaseDatabase):
    """履歴：隣接機器が変わった/消えた時だけ1行追加"""
    __tablename__ = "cdp_neighbor_history"

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    local_interface = Column(String(32), nullable=False)
    neighbor_hostname_raw = Column(String(128), nullable=False)
    neighbor_interface = Column(String(32), nullable=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    switch = relationship("Switch")