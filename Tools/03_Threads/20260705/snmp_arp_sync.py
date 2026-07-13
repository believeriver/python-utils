"""
コアスイッチ(L3)からSNMP経由でARPテーブルを取得し、DBに保存するモジュール。
L3スイッチにはSSHで直接ログインできないため、この経路を使う。
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config, setup_logger
from models.switch import Switch
from models.arp_entry import ArpEntry
from snmp.arp_collector import get_arp_entries

logger = setup_logger("snmp_arp_sync", Config.LEVEL)


def collect_arp_via_snmp(core_switches: list) -> None:
    """
    core_switches: [{"hostname": str, "host": str, "community": str}, ...]
    (config.py の Config.CORE_SWITCHES を想定)
    """
    for sw in core_switches:
        switch = Switch.fetch_by_hostname(sw["hostname"])
        if switch is None:
            logger.warning(f"Switch not found in DB: {sw['hostname']} (先にInventory登録が必要です)")
            continue

        try:
            entries = get_arp_entries(
                host=sw["host"],
                community=sw["community"],
                label=sw["hostname"],
            )
        except Exception as e:
            logger.error(f"SNMP ARP収集に失敗しました: {sw['hostname']} ({sw['host']}): {e}")
            continue

        collected = [
            {
                "vlan": e.vlan_id,
                "ip_address": e.ip_address,
                "mac_address": e.mac_address,
            }
            for e in entries
            if e.vlan_id is not None  # VLAN番号が特定できないエントリは除外
        ]

        ArpEntry.sync_from_collection(switch["id"], collected)
        logger.info(f"arp(snmp) saved: {sw['hostname']} ({len(collected)} entries)")