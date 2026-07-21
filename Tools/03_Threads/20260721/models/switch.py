import sys
import os
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Boolean

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, setup_logger
from models.db import BaseDatabase, database, db_write_lock

logger = setup_logger("Switch", Config.LEVEL)


class Switch(BaseDatabase):
    __tablename__ = "switches"

    hostname = Column(String(64), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=False)
    hardware_model = Column(String(32), nullable=False)
    base_mac_address = Column(String(17), nullable=True)
    # service_tag = Column(String(32), unique=True, nullable=True)
    service_tag = Column(String(32), nullable=True)  # unique=True を削除
    firmware_version = Column(String(32), nullable=True)
    location = Column(String(128), nullable=True)
    switch_type = Column(String(8), nullable=False)     # "L2" / "L3"
    role = Column(String(16), nullable=False)            # "floor" / "edge" / "core"
    data_vlan = Column(Integer, nullable=True)
    ntp_servers = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    @staticmethod
    def fetch_all() -> List[dict]:
        """is_activeに関わらず全件返す(一覧・検索画面用)"""
        session = database.connect_db()
        rows = session.query(Switch).all()
        result = [{
            "id": row.id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
            "hardware_model": row.hardware_model,
            "base_mac_address": row.base_mac_address,
            "service_tag": row.service_tag,
            "firmware_version": row.firmware_version,
            "location": row.location,
            "switch_type": row.switch_type,
            "role": row.role,
            "is_active": row.is_active,
            "updated_at": row.updated_at,
        } for row in rows]
        session.close()
        return result

    @staticmethod
    def get_or_create(hostname: str, ip_address: str, hardware_model: str,
                       switch_type: str, role: str, **kwargs) -> "Switch":
        with db_write_lock:
            session = database.connect_db()
            row = session.query(Switch).filter(Switch.hostname == hostname).first()

            if row:
                row.ip_address = ip_address
                row.hardware_model = hardware_model
                row.switch_type = switch_type
                row.role = role
                for key, value in kwargs.items():
                    setattr(row, key, value)
                session.add(row)
                session.commit()
                row = session.query(Switch).filter(Switch.hostname == hostname).first()
                logger.info(f"updated switch: {hostname}")
            else:
                row = Switch(
                    hostname=hostname, ip_address=ip_address, hardware_model=hardware_model,
                    switch_type=switch_type, role=role, **kwargs,
                )
                session.add(row)
                session.commit()
                row = session.query(Switch).filter(Switch.hostname == hostname).first()
                logger.info(f"created switch: {hostname}")

            session.close()
            return row

    @staticmethod
    def fetch_all_active() -> List[dict]:
        session = database.connect_db()
        rows = session.query(Switch).filter(Switch.is_active == True).all()
        result = [{
            "id": row.id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
            "location": row.location,
            "role": row.role,
        } for row in rows]
        session.close()
        return result

    @staticmethod
    def fetch_by_hostname(hostname: str) -> Optional[dict]:
        session = database.connect_db()
        row = session.query(Switch).filter(Switch.hostname == hostname).first()
        if row is None:
            session.close()
            return None
        result = {
            "id": row.id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
            "hardware_model": row.hardware_model,
            "base_mac_address": row.base_mac_address,
            "service_tag": row.service_tag,
            "firmware_version": row.firmware_version,
            "location": row.location,
            "role": row.role,
        }
        session.close()
        return result

    @staticmethod
    # 2026.07.14 SNMP経由でARP収集する際に、ホスト名からスイッチ情報を取得するためのメソッドを追加
    def fetch_by_hostname_for_snmp(hostname: str) -> Optional[dict]:
        session = database.connect_db()
        row = session.query(Switch).filter(Switch.hostname == hostname).first()
        if row is None:
            session.close()
            return None
        result = {
            "id": row.id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
        }
        session.close()
        return result

    @staticmethod
    def update_hardware_info(hostname: str, **fields) -> None:
        """show version/show inventoryの結果でハードウェア情報を上書きする"""
        with db_write_lock:
            session = database.connect_db()
            row = session.query(Switch).filter(Switch.hostname == hostname).first()
            if row is None:
                session.close()
                logger.warning(f"update_hardware_info: switch not found: {hostname}")
                return

            for key, value in fields.items():
                if value:  # 取得できなかった項目(None)で上書きしない
                    setattr(row, key, value)

            session.commit()
            session.close()
            logger.info(f"hardware info updated: {hostname}")

    @staticmethod
    def fetch_by_ip(ip_address: str) -> Optional[dict]:
        """IPアドレスからホスト名を逆引きする(is_active=Trueのみ対象)"""
        session = database.connect_db()
        row = session.query(Switch).filter(
            Switch.ip_address == ip_address,
            Switch.is_active == True,
        ).first()
        if row is None:
            session.close()
            return None
        result = {
            "id": row.id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
            "role": row.role,
        }
        session.close()
        return result

    @staticmethod
    def find_duplicate_service_tags() -> List[dict]:
        """is_active=Trueのスイッチ間で、service_tagが重複しているものを検出する"""
        session = database.connect_db()
        rows = session.query(Switch).filter(
            Switch.is_active == True,
            Switch.service_tag.isnot(None),
        ).all()

        from collections import defaultdict
        tag_map = defaultdict(list)
        for row in rows:
            tag_map[row.service_tag].append(row.hostname)

        session.close()

        return [
            {"service_tag": tag, "hostnames": hosts}
            for tag, hosts in tag_map.items() if len(hosts) > 1
        ]
