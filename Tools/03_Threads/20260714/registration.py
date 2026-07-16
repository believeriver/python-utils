import csv
import sys
import time
import os

from thread_worker import set_queue, main_threads
from utils import SwitchListDataset
from config import Config, setup_logger
from reporter import ReporterSample

from concrete_executor import (
    FetchInventoryExecutor,
    FetchCdpExecutor,
    FetchMacTableExecutor,
    FetchArpExecutor,
)
from parsers.parse import (
    parse_show_version,
    parse_show_inventory,
    parse_cdp_neighbors_detail,
    parse_mac_address_table,
    parse_arp_table,
)

from models.switch import Switch
from models.cdp_neighbor import CdpNeighbor
from models.mac_address import MacAddressEntry
from models.arp_entry import ArpEntry

logger = setup_logger("registration", Config.LEVEL)

REQUIRED_FIELDS = ["hostname", "ipaddr", "switch_type", "role"]
VALID_SWITCH_TYPES = {"L2", "L3"}
VALID_ROLES = {"floor", "edge", "core"}


def _clean_row(row: dict) -> dict:
    """列名・値の前後の空白を除去する"""
    return {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _validate_row(row: dict) -> list:
    """
    1行分のバリデーションを行い、問題点のリストを返す(空リストなら問題なし)。
    """
    errors = []

    for field in REQUIRED_FIELDS:
        if not row.get(field):
            errors.append(f"必須項目が空です: {field}")

    switch_type = row.get("switch_type")
    if switch_type and switch_type not in VALID_SWITCH_TYPES:
        errors.append(f"switch_typeの値が不正です: '{switch_type}' (許容値: {VALID_SWITCH_TYPES})")

    role = row.get("role")
    if role and role not in VALID_ROLES:
        errors.append(f"roleの値が不正です: '{role}' (許容値: {VALID_ROLES})")

    return errors


def register_switches_from_csv(csv_path: str) -> dict:
    """
    ①CSVからスイッチを仮登録する(スレッド化不要)。
    不備のある行はスキップし、記録する。

    戻り値: {
        "succeeded": [hostname, ...],
        "failed": [{"row_number": int, "hostname": str, "errors": [str, ...]}, ...]
    }
    """
    succeeded = []
    failed = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row_number, raw_row in enumerate(reader, start=2):  # ヘッダーが1行目なので実データは2行目から
            row = _clean_row(raw_row)
            errors = _validate_row(row)

            if errors:
                failed.append({
                    "row_number": row_number,
                    "hostname": row.get("hostname") or "(不明)",
                    "errors": errors,
                })
                logger.warning(f"[SKIP] row={row_number} hostname={row.get('hostname')} errors={errors}")
                continue

            Switch.get_or_create(
                hostname=row["hostname"],
                ip_address=row["ipaddr"],
                hardware_model="unknown",
                switch_type=row["switch_type"],
                role=row["role"],
                location=row.get("location") or None,
            )
            succeeded.append(row["hostname"])

    return {"succeeded": succeeded, "failed": failed}


def print_registration_report(result: dict) -> None:
    print("=" * 60)
    print(f"[INFO] 登録成功: {len(result['succeeded'])}件")
    print(f"[INFO] 登録失敗: {len(result['failed'])}件")

    if result["failed"]:
        print("-" * 60)
        print("[WARN] 以下の行はスキップされました:")
        for item in result["failed"]:
            print(f"  行{item['row_number']} (hostname={item['hostname']}):")
            for err in item["errors"]:
                print(f"    - {err}")
    print("=" * 60)


def collect_hardware_info(targets: list, workers: int = Config.MAX_WORKERS) -> None:
    q = set_queue(_targets=targets)
    results = main_threads(
        _q=q,
        workers=workers,
        executor_cls=FetchInventoryExecutor,
        reporter_cls=ReporterSample,
        level=Config.LEVEL,
    )

    for res in results:
        for hostname, lines in res.items():
            if not lines:
                logger.warning(f"収集結果なし: {hostname}")
                continue
            info = {}
            info.update(parse_show_version(lines))
            info.update(parse_show_inventory(lines))
            Switch.update_hardware_info(hostname, **info)
            logger.info(f"hardware info updated: {hostname} -> {info}")


def collect_cdp_neighbors(targets: list, workers: int = Config.MAX_WORKERS) -> None:
    q = set_queue(_targets=targets)
    results = main_threads(
        _q=q,
        workers=workers,
        executor_cls=FetchCdpExecutor,
        reporter_cls=ReporterSample,
        level=Config.LEVEL,
    )

    for res in results:
        for hostname, lines in res.items():
            if not lines:
                logger.warning(f"CDP収集結果なし: {hostname}")
                continue

            switch = Switch.fetch_by_hostname(hostname)
            if switch is None:
                logger.warning(f"Switch not found in DB: {hostname}")
                continue

            neighbors = parse_cdp_neighbors_detail(lines)
            CdpNeighbor.sync_from_collection(switch["id"], neighbors)
            logger.info(f"cdp saved: {hostname} ({len(neighbors)} neighbors)")


def collect_mac_address_table(targets: list, workers: int = Config.MAX_WORKERS) -> None:
    q = set_queue(_targets=targets)
    results = main_threads(
        _q=q,
        workers=workers,
        executor_cls=FetchMacTableExecutor,
        reporter_cls=ReporterSample,
        level=Config.LEVEL,
    )

    for res in results:
        for hostname, lines in res.items():
            if not lines:
                logger.warning(f"MACテーブル収集結果なし: {hostname}")
                continue

            switch = Switch.fetch_by_hostname(hostname)
            if switch is None:
                logger.warning(f"Switch not found in DB: {hostname}")
                continue

            entries = parse_mac_address_table(lines)
            MacAddressEntry.sync_from_collection(switch["id"], entries)
            logger.info(f"mac saved: {hostname} ({len(entries)} entries)")


def collect_arp_table(targets: list, workers: int = Config.MAX_WORKERS) -> None:
    q = set_queue(_targets=targets)
    results = main_threads(
        _q=q,
        workers=workers,
        executor_cls=FetchArpExecutor,
        reporter_cls=ReporterSample,
        level=Config.LEVEL,
    )

    for res in results:
        for hostname, lines in res.items():
            if not lines:
                logger.warning(f"ARP収集結果なし: {hostname}")
                continue

            switch = Switch.fetch_by_hostname(hostname)
            if switch is None:
                logger.warning(f"Switch not found in DB: {hostname}")
                continue

            entries = parse_arp_table(lines)
            ArpEntry.sync_from_collection(switch["id"], entries)
            logger.info(f"arp saved: {hostname} ({len(entries)} entries)")


def main(argv):
    start = time.time()
    step = argv[0] if argv else "1"

    cur_dir = os.getcwd()
    targets_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.REGISTER_FILE)

    if step == "1":
        result = register_switches_from_csv(targets_file)
        print_registration_report(result)

    elif step == "2":
        # print("[INFO] ステップ2(実機収集)は未実装です")
        dataset = SwitchListDataset(targets_file)
        collect_hardware_info(targets=dataset.targets_list, workers=Config.MAX_WORKERS)

    elif step == "3":
        dataset = SwitchListDataset(targets_file)
        collect_cdp_neighbors(targets=dataset.targets_list, workers=Config.MAX_WORKERS)

    elif step == "4":
        dataset = SwitchListDataset(targets_file)
        collect_mac_address_table(targets=dataset.targets_list, workers=Config.MAX_WORKERS)

    elif step == "5":
        dataset = SwitchListDataset(targets_file)
        collect_arp_table(targets=dataset.targets_list, workers=Config.MAX_WORKERS)

    elif step == "6":
        from snmp_arp_sync import collect_arp_via_snmp
        collect_arp_via_snmp(Config.CORE_SWITCHES)

    elif step == "7":
        from utils import LivenessTargetDataset
        from liveness_check import run_liveness_check
        liveness_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.LIVENESS_TARGET_CSV)
        dataset = LivenessTargetDataset(liveness_file)
        run_liveness_check(dataset.targets_list, workers=20)

    else:
        print("[ERROR] 引数は 1,2,3,4,5 のいずれかを指定してください")
        exit(1)

    elapsed = time.time() - start
    print(f"[INFO] Elapsed: {elapsed:.2f} seconds")


if __name__ == "__main__":
    # python registration.py 1 : regist switches from CSV
    # python registration.py 2 : collect hardware info from registered switches
    main(sys.argv[1:])