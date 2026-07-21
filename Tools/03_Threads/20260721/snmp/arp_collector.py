"""
SNMP経由でコアスイッチからARPテーブルを取得するモジュール。
ipNetToMediaTable (1.3.6.1.2.1.4.22) を使用。
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from pysnmp.hlapi import (
    CommunityData, ContextData, ObjectIdentity, ObjectType,
    SnmpEngine, UdpTransportTarget, nextCmd,
)


# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------

@dataclass
class ArpEntry:
    switch_label: str       # 表示名（設定ファイル由来）
    switch_host:  str       # IPまたはホスト名
    vlan_id:      Optional[int]
    interface:    str       # "Vlan100" など
    ip_address:   str
    mac_address:  str       # "xx:xx:xx:xx:xx:xx"


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------

def _mac_to_str(mac_val) -> str:
    """pysnmp の OctetString を "xx:xx:xx:xx:xx:xx" 形式に変換"""
    try:
        raw = bytes(mac_val)
        if len(raw) == 6:
            return ':'.join(f'{b:02x}' for b in raw)
    except Exception:
        pass
    return str(mac_val)


def _snmp_walk(host: str, community: str, oid: str, port: int) -> dict[str, object]:
    """指定OID以下をwalkしてdict {oid_str: value} で返す"""
    result = {}
    for (err_indication, err_status, _, var_binds) in nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),          # SNMPv2c
        UdpTransportTarget((host, port), timeout=3, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False,
    ):
        if err_indication or err_status:
            raise RuntimeError(
                err_indication or err_status.prettyPrint()
            )
        for var_bind in var_binds:
            result[str(var_bind[0])] = var_bind[1]
    return result


# ---------------------------------------------------------------------------
# 公開API
# ---------------------------------------------------------------------------

def get_arp_entries(
    host: str,
    community: str,
    label: str = "",
    port: int = 161,
) -> list[ArpEntry]:
    """
    1台のスイッチからARPエントリ一覧を取得する。

    使用OID:
      1.3.6.1.2.1.4.22.1.2  ipNetToMediaPhysAddress
        └── suffix: {ifIndex}.{a.b.c.d}
      1.3.6.1.2.1.2.2.1.2   ifDescr
        └── suffix: {ifIndex}
    """
    OID_MAC    = "1.3.6.1.2.1.4.22.1.2"
    OID_IFDESC = "1.3.6.1.2.1.2.2.1.2"

    # ifIndex -> インターフェース名
    if_descr_raw = _snmp_walk(host, community, OID_IFDESC, port)
    if_map: dict[str, str] = {}
    for oid_str, val in if_descr_raw.items():
        idx = oid_str.rsplit(".", 1)[-1]
        if_map[idx] = str(val)

    # MACアドレステーブル
    mac_raw = _snmp_walk(host, community, OID_MAC, port)

    entries: list[ArpEntry] = []
    for oid_str, mac_val in mac_raw.items():
        # OID末尾: {ifIndex}.{a.b.c.d}
        suffix = oid_str[len(OID_MAC) + 1:]
        parts = suffix.split(".", 1)
        if len(parts) != 2:
            continue
        if_index, ip_addr = parts

        if_name = if_map.get(if_index, f"ifIndex={if_index}")
        m = re.search(r"[Vv]lan(\d+)", if_name)
        vlan_id = int(m.group(1)) if m else None

        entries.append(ArpEntry(
            switch_label=label or host,
            switch_host=host,
            vlan_id=vlan_id,
            interface=if_name,
            ip_address=ip_addr,
            mac_address=_mac_to_str(mac_val),
        ))

    return entries
