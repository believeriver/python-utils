import sys
import os
import datetime
from typing import List, Optional, Dict

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, setup_logger
from models.db import BaseDatabase, database, db_write_lock
from models.switch import Switch

logger = setup_logger("MacAddressEntry", Config.LEVEL)


class MacAddressEntry(BaseDatabase):
    """現在の状態：(switch, vlan, mac)につき1行のみ"""
    __tablename__ = "mac_address_entries"
    __table_args__ = (
        UniqueConstraint("switch_id", "vlan", "mac_address", name="uq_switch_vlan_mac"),
    )

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    vlan = Column(Integer, nullable=False)
    mac_address = Column(String(17), nullable=False)
    port = Column(String(32), nullable=False)

    switch = relationship("Switch")

    @staticmethod
    def sync_from_collection(switch_id: int, collected_entries: List[Dict]) -> None:
        """
        1スイッチ分のshow mac address-table結果をまとめて反映する。
        collected_entries: [{"vlan": 10, "mac_address": "aa:bb:...", "port": "Gi1/0/1"}, ...]

        - 新規MAC      → 追加
        - ポート変化なし → updated_atだけ更新
        - ポート変化あり → 旧区間をhistoryに記録して更新
        - 今回出てこなかったMAC → 旧区間をhistoryに記録して削除
        """
        with db_write_lock:
            session = database.connect_db()
            now = datetime.datetime.utcnow()

            existing_rows = session.query(MacAddressEntry).filter(
                MacAddressEntry.switch_id == switch_id
            ).all()
            existing_map = {(row.vlan, row.mac_address): row for row in existing_rows}

            seen_keys = set()

            for entry in collected_entries:
                key = (entry["vlan"], entry["mac_address"])
                seen_keys.add(key)
                row = existing_map.get(key)

                if row is None:
                    session.add(MacAddressEntry(
                        switch_id=switch_id, vlan=entry["vlan"],
                        mac_address=entry["mac_address"], port=entry["port"],
                    ))
                    logger.info(f"new mac: {entry['mac_address']} vlan{entry['vlan']} -> {entry['port']}")

                elif row.port == entry["port"]:
                    row.updated_at = now

                else:
                    session.add(MacAddressHistory(
                        switch_id=row.switch_id, vlan=row.vlan, mac_address=row.mac_address,
                        port=row.port, valid_from=row.created_at, valid_to=now,
                    ))
                    logger.info(
                        f"mac moved: {row.mac_address} vlan{row.vlan} {row.port} -> {entry['port']}"
                    )
                    row.port = entry["port"]
                    row.created_at = now
                    row.updated_at = now

            # 今回出てこなかったMAC = 消えたとみなしてhistory化
            for key, row in existing_map.items():
                if key not in seen_keys:
                    session.add(MacAddressHistory(
                        switch_id=row.switch_id, vlan=row.vlan, mac_address=row.mac_address,
                        port=row.port, valid_from=row.created_at, valid_to=now,
                    ))
                    logger.info(f"mac disappeared: {row.mac_address} vlan{row.vlan} (was {row.port})")
                    session.delete(row)

            session.commit()
            session.close()

    @staticmethod
    def fetch_by_mac(mac_address: str) -> Optional[dict]:
        session = database.connect_db()
        row = session.query(MacAddressEntry).filter(
            MacAddressEntry.mac_address == mac_address
        ).first()
        if row is None:
            session.close()
            return None
        result = {
            "switch_hostname": row.switch.hostname,
            "location": row.switch.location,
            "vlan": row.vlan,
            "port": row.port,
            "first_seen": row.created_at,
            "last_seen": row.updated_at,
        }
        session.close()
        return result


class MacAddressHistory(BaseDatabase):
    """履歴：ポート移動・消失があった時だけ1行追加"""
    __tablename__ = "mac_address_history"

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    vlan = Column(Integer, nullable=False)
    mac_address = Column(String(17), nullable=False)
    port = Column(String(32), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    switch = relationship("Switch")

    @staticmethod
    def fetch_by_mac(mac_address: str) -> List[dict]:
        """Streamlitの履歴表示用に、古い順で全件返す"""
        session = database.connect_db()
        rows = session.query(MacAddressHistory).filter(
            MacAddressHistory.mac_address == mac_address
        ).order_by(MacAddressHistory.valid_from.asc()).all()

        result = [{
            "switch_hostname": row.switch.hostname,
            "port": row.port,
            "vlan": row.vlan,
            "valid_from": row.valid_from,
            "valid_to": row.valid_to,
        } for row in rows]
        session.close()
        return result