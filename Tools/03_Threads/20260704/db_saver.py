from abc import ABC, abstractmethod
from typing import List

from models.switch import Switch
from models.mac_address import MacAddressEntry
from models.cdp_neighbor import CdpNeighbor
from models.arp_entry import ArpEntry
from parsers.parse import (
    parse_mac_address_table,
    parse_cdp_neighbors_detail,
    parse_arp_table,
    parse_show_version,
    parse_show_inventory,
)


# -----------------------------
# DB Saver Interface
# -----------------------------

class IDBSaverInterface(ABC):
    @staticmethod
    @abstractmethod
    def save_results(results: List[dict]) -> None:
        pass


# -----------------------------
# Concrete DB Savers
# -----------------------------

class MacAddressDBSaver(IDBSaverInterface):
    @staticmethod
    def save_results(results: List[dict]) -> None:
        """
        results: [{"sw-3f-edge-01": ["line1", "line2", ...]}, ...]
        """
        for res in results:
            for hostname, lines in res.items():
                if not lines:
                    continue

                switch = Switch.fetch_by_hostname(hostname)
                if switch is None:
                    print(f"[WARN] Switch not found in DB: {hostname}")
                    continue

                entries = parse_mac_address_table(lines)
                MacAddressEntry.sync_from_collection(switch["id"], entries)
                print(f"[INFO] mac saved: {hostname} ({len(entries)} entries)")


class CdpNeighborDBSaver(IDBSaverInterface):
    @staticmethod
    def save_results(results: List[dict]) -> None:
        for res in results:
            for hostname, lines in res.items():
                if not lines:
                    continue

                switch = Switch.fetch_by_hostname(hostname)
                if switch is None:
                    print(f"[WARN] Switch not found in DB: {hostname}")
                    continue

                neighbors = parse_cdp_neighbors_detail(lines)
                CdpNeighbor.sync_from_collection(switch["id"], neighbors)
                print(f"[INFO] cdp saved: {hostname} ({len(neighbors)} neighbors)")


class ArpDBSaver(IDBSaverInterface):
    @staticmethod
    def save_results(results: List[dict]) -> None:
        for res in results:
            for hostname, lines in res.items():
                if not lines:
                    continue

                switch = Switch.fetch_by_hostname(hostname)
                if switch is None:
                    print(f"[WARN] Switch not found in DB: {hostname}")
                    continue

                entries = parse_arp_table(lines)
                ArpEntry.sync_from_collection(switch["id"], entries)
                print(f"[INFO] arp saved: {hostname} ({len(entries)} entries)")


class InventoryDBSaver(IDBSaverInterface):
    @staticmethod
    def save_results(results: List[dict]) -> None:
        for res in results:
            for hostname, lines in res.items():
                if not lines:
                    continue

                version_lines = lines  # show version + show inventory が混在した全行
                info = {}
                info.update(parse_show_version(version_lines))
                info.update(parse_show_inventory(version_lines))

                Switch.update_hardware_info(hostname, **info)
                print(f"[INFO] inventory saved: {hostname} -> {info}")
