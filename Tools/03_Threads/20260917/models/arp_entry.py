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

logger = setup_logger("ArpEntry", Config.LEVEL)


class ArpEntry(BaseDatabase):
    """現在の状態：(switch, vlan, ip_address)につき1行のみ"""
    __tablename__ = "arp_entries"
    __table_args__ = (
        UniqueConstraint("switch_id", "vlan", "ip_address", name="uq_switch_vlan_ip"),
    )

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    vlan = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=False)
    mac_address = Column(String(17), nullable=False)

    switch = relationship("Switch")

    @staticmethod
    def sync_from_collection(switch_id: int, collected_entries: List[Dict]) -> None:
        """
        1回分のARP収集結果をまとめて反映する。
        collected_entries: [{"vlan": 10, "ip_address": "10.1.1.1", "mac_address": "aa:bb:..."}, ...]

        - 新規IP          → 追加
        - MAC変化なし      → updated_atだけ更新
        - MACが変わった    → 旧区間をhistoryに記録して更新
        - 今回出てこなかった → 旧区間をhistoryに記録して削除
        """
        with db_write_lock:
            session = database.connect_db()
            now = datetime.datetime.utcnow()

            existing_rows = session.query(ArpEntry).filter(
                ArpEntry.switch_id == switch_id
            ).all()
            existing_map = {(row.vlan, row.ip_address): row for row in existing_rows}

            seen_keys = set()

            for entry in collected_entries:
                key = (entry["vlan"], entry["ip_address"])
                seen_keys.add(key)
                row = existing_map.get(key)

                if row is None:
                    session.add(ArpEntry(
                        switch_id=switch_id,
                        vlan=entry["vlan"],
                        ip_address=entry["ip_address"],
                        mac_address=entry["mac_address"],
                    ))
                    logger.info(f"new arp: {entry['ip_address']} -> {entry['mac_address']} vlan{entry['vlan']}")

                elif row.mac_address == entry["mac_address"]:
                    # 変化なし → 確認時刻だけ更新
                    row.updated_at = now

                else:
                    # MACが変わった（機器交換・IPの付け替え等）
                    session.add(ArpHistory(
                        switch_id=row.switch_id,
                        vlan=row.vlan,
                        ip_address=row.ip_address,
                        mac_address=row.mac_address,
                        valid_from=row.created_at,
                        valid_to=now,
                    ))
                    logger.info(
                        f"arp changed: {row.ip_address} vlan{row.vlan} "
                        f"{row.mac_address} -> {entry['mac_address']}"
                    )
                    row.mac_address = entry["mac_address"]
                    row.created_at = now
                    row.updated_at = now

            # 今回出てこなかったIP = ARPエージング等で消えたとみなしてhistory化
            for key, row in existing_map.items():
                if key not in seen_keys:
                    session.add(ArpHistory(
                        switch_id=row.switch_id,
                        vlan=row.vlan,
                        ip_address=row.ip_address,
                        mac_address=row.mac_address,
                        valid_from=row.created_at,
                        valid_to=now,
                    ))
                    logger.info(
                        f"arp disappeared: {row.ip_address} vlan{row.vlan} (was {row.mac_address})"
                    )
                    session.delete(row)

            session.commit()
            session.close()

    @staticmethod
    def fetch_by_ip(ip_address: str) -> Optional[dict]:
        """IP→MAC・スイッチの現在の対応を返す"""
        session = database.connect_db()
        row = session.query(ArpEntry).filter(
            ArpEntry.ip_address == ip_address
        ).first()
        if row is None:
            session.close()
            return None
        result = {
            "switch_hostname": row.switch.hostname,
            "vlan": row.vlan,
            "ip_address": row.ip_address,
            "mac_address": row.mac_address,
            "first_seen": row.created_at,
            "last_seen": row.updated_at,
        }
        session.close()
        return result

    @staticmethod
    def fetch_by_mac(mac_address: str) -> List[dict]:
        """MAC→IP一覧を返す（1MACに複数IPが紐づく場合もある）"""
        session = database.connect_db()
        rows = session.query(ArpEntry).filter(
            ArpEntry.mac_address == mac_address
        ).all()
        result = [{
            "switch_hostname": row.switch.hostname,
            "vlan": row.vlan,
            "ip_address": row.ip_address,
            "mac_address": row.mac_address,
            "first_seen": row.created_at,
            "last_seen": row.updated_at,
        } for row in rows]
        session.close()
        return result

    @staticmethod
    def fetch_mac_to_ip_map(mac_addresses: List[str]) -> Dict[str, List[str]]:
        """MACアドレスのリストを渡し、MAC→IPアドレス一覧の対応表を返す(1MACに複数IPの可能性あり)"""
        if not mac_addresses:
            return {}
        session = database.connect_db()
        rows = session.query(ArpEntry).filter(
            ArpEntry.mac_address.in_(mac_addresses)
        ).all()
        result: Dict[str, List[str]] = {}
        for row in rows:
            result.setdefault(row.mac_address, []).append(row.ip_address)
        session.close()
        return result


class ArpHistory(BaseDatabase):
    """履歴：MACが変わった・消えた時だけ1行追加"""
    __tablename__ = "arp_history"

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    vlan = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=False)
    mac_address = Column(String(17), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    switch = relationship("Switch")

    @staticmethod
    def fetch_by_ip(ip_address: str) -> List[dict]:
        """IP指定で過去のMAC変化履歴を古い順に返す"""
        session = database.connect_db()
        rows = session.query(ArpHistory).filter(
            ArpHistory.ip_address == ip_address
        ).order_by(ArpHistory.valid_from.asc()).all()
        result = [{
            "switch_hostname": row.switch.hostname,
            "vlan": row.vlan,
            "ip_address": row.ip_address,
            "mac_address": row.mac_address,
            "valid_from": row.valid_from,
            "valid_to": row.valid_to,
        } for row in rows]
        session.close()
        return result