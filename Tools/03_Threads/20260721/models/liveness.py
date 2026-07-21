import sys
import os
import datetime
from typing import List, Optional, Dict

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, setup_logger
from models.db import BaseDatabase, database, db_write_lock

logger = setup_logger("Liveness", Config.LEVEL)


class Liveness(BaseDatabase):
    """現在の死活監視状態：switchにつき1行のみ"""
    __tablename__ = "liveness"

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False, unique=True)
    ping_ok = Column(Boolean, nullable=False)
    ping_rtt_ms = Column(Float, nullable=True)
    ssh_ok = Column(Boolean, nullable=False)
    ssh_error = Column(String(256), nullable=True)
    ping_since = Column(DateTime, nullable=False)   # 現在のping_ok状態が始まった時刻
    checked_at = Column(DateTime, nullable=False)     # 直近の確認時刻

    switch = relationship("Switch")

    @staticmethod
    def upsert(switch_id: int, ping_ok: bool, ssh_ok: bool,
               ping_rtt_ms: float = None, ssh_error: str = None) -> None:
        with db_write_lock:
            session = database.connect_db()
            now = datetime.datetime.utcnow()

            row = session.query(Liveness).filter(Liveness.switch_id == switch_id).first()

            if row is None:
                # 初回はそのまま新規作成(履歴は発生しない)
                session.add(Liveness(
                    switch_id=switch_id, ping_ok=ping_ok, ping_rtt_ms=ping_rtt_ms,
                    ssh_ok=ssh_ok, ssh_error=ssh_error,
                    ping_since=now, checked_at=now,
                ))
                logger.info(f"liveness new: switch_id={switch_id} ping={ping_ok} ssh={ssh_ok}")

            elif row.ping_ok == ping_ok:
                # Ping状態に変化なし → checked_atとRTT/SSH結果だけ更新
                row.ping_rtt_ms = ping_rtt_ms
                row.ssh_ok = ssh_ok
                row.ssh_error = ssh_error
                row.checked_at = now

            else:
                # Ping状態が変化した(成功→失敗 or 失敗→成功) → 直前の区間を履歴化
                session.add(LivenessHistory(
                    switch_id=row.switch_id,
                    ping_ok=row.ping_ok,
                    valid_from=row.ping_since,
                    valid_to=now,
                ))
                logger.info(
                    f"liveness changed: switch_id={switch_id} "
                    f"ping {row.ping_ok} -> {ping_ok} (継続時間: {row.ping_since} 〜 {now})"
                )
                row.ping_ok = ping_ok
                row.ping_rtt_ms = ping_rtt_ms
                row.ssh_ok = ssh_ok
                row.ssh_error = ssh_error
                row.ping_since = now
                row.checked_at = now

            session.commit()
            session.close()

    @staticmethod
    def fetch_all() -> List[dict]:
        session = database.connect_db()
        rows = session.query(Liveness).all()
        result = [{
            "switch_id": row.switch_id,
            "hostname": row.switch.hostname,
            "ping_ok": row.ping_ok,
            "ping_rtt_ms": row.ping_rtt_ms,
            "ssh_ok": row.ssh_ok,
            "ssh_error": row.ssh_error,
            "ping_since": row.ping_since,
            "checked_at": row.checked_at,
        } for row in rows]
        session.close()
        return result

    @staticmethod
    def fetch_by_switch_id(switch_id: int) -> Optional[dict]:
        session = database.connect_db()
        row = session.query(Liveness).filter(Liveness.switch_id == switch_id).first()
        if row is None:
            session.close()
            return None
        result = {
            "ping_ok": row.ping_ok,
            "ping_rtt_ms": row.ping_rtt_ms,
            "ssh_ok": row.ssh_ok,
            "ssh_error": row.ssh_error,
            "ping_since": row.ping_since,
            "checked_at": row.checked_at,
        }
        session.close()
        return result


class LivenessHistory(BaseDatabase):
    """履歴：Ping状態(成功/失敗)が切り替わった区間を記録"""
    __tablename__ = "liveness_history"

    switch_id = Column(Integer, ForeignKey("switches.id"), nullable=False)
    ping_ok = Column(Boolean, nullable=False)   # その区間、成功していたか失敗していたか
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    switch = relationship("Switch")

    @staticmethod
    def fetch_by_switch_id(switch_id: int) -> List[dict]:
        """指定スイッチのPing状態変化履歴を古い順に返す"""
        session = database.connect_db()
        rows = session.query(LivenessHistory).filter(
            LivenessHistory.switch_id == switch_id
        ).order_by(LivenessHistory.valid_from.asc()).all()
        result = [{
            "ping_ok": row.ping_ok,
            "valid_from": row.valid_from,
            "valid_to": row.valid_to,
        } for row in rows]
        session.close()
        return result
