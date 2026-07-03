import re
from typing import List, Dict


def parse_mac_address_table(lines: List[str]) -> List[Dict]:
    """
    show mac address-table のCLI出力行リストを構造化データに変換する。

    Cisco IOS 例:
          10    aabb.ccdd.ee01    DYNAMIC     Gi1/0/1
    """
    result = []
    pattern = re.compile(
        r"^\s*(\d+)\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+(\S+)"
    )
    for line in lines:
        m = pattern.match(line)
        if not m:
            continue
        vlan = int(m.group(1))
        mac_cisco = m.group(2)                          # "aabb.ccdd.ee01" 形式
        mac = _normalize_mac(mac_cisco)
        port = m.group(3)
        if port.lower() in ("cpu", "drop"):             # システム用エントリは除外
            continue
        result.append({"vlan": vlan, "mac_address": mac, "port": port})
    return result


def parse_cdp_neighbors_detail(lines: List[str]) -> List[Dict]:
    """
    show cdp neighbors detail のCLI出力行リストを構造化データに変換する。
    1ネイバーのブロックを抽出して辞書化する。
    """
    result = []
    current = {}
    text = "\n".join(lines)

    # ネイバーブロックの区切りは "-------------------------"
    blocks = re.split(r"-{10,}", text)

    for block in blocks:
        neighbor_raw = _extract(block, r"Device ID:\s*(\S+)")
        local_if = _extract(block, r"Interface:\s*(\S+?),")
        neighbor_if = _extract(block, r"Port ID \(outgoing port\):\s*(\S+)")
        platform = _extract(block, r"Platform:\s*(.+?),")
        chassis_mac = _extract(block, r"(?i)chassis id[:\s]+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})")

        if not neighbor_raw or not local_if:
            continue

        result.append({
            "local_interface": local_if,
            "neighbor_hostname_raw": neighbor_raw,
            "neighbor_interface": neighbor_if,
            "neighbor_platform": platform,
            "neighbor_chassis_mac": _normalize_mac(chassis_mac) if chassis_mac else None,
        })

    return result


def parse_arp_table(lines: List[str]) -> List[Dict]:
    """
    show ip arp のCLI出力行リストを構造化データに変換する。

    Cisco IOS 例:
    Internet  10.1.10.1   0   aabb.ccdd.ee01  ARPA  Vlan10
    """
    result = []
    pattern = re.compile(
        r"Internet\s+(\d+\.\d+\.\d+\.\d+)\s+\S+\s+"
        r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+Vlan(\d+)"
    )
    for line in lines:
        m = pattern.match(line.strip())
        if not m:
            continue
        result.append({
            "ip_address": m.group(1),
            "mac_address": _normalize_mac(m.group(2)),
            "vlan": int(m.group(3)),
        })
    return result


def _extract(text: str, pattern: str) -> str:
    """正規表現で1件だけ抽出するヘルパー"""
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def _normalize_mac(mac: str) -> str:
    """Cisco形式(aabb.ccdd.ee01) → コロン区切り(aa:bb:cc:dd:ee:01)に正規化"""
    if not mac:
        return ""
    hex_only = re.sub(r"[^0-9a-fA-F]", "", mac).lower()
    if len(hex_only) != 12:
        return mac  # 変換できない場合はそのまま返す
    return ":".join(hex_only[i:i+2] for i in range(0, 12, 2))
