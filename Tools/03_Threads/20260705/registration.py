import csv
import sys
import time
import os
import logging

from config import Config, setup_logger
from models.switch import Switch
from thread_worker import set_queue, main_threads
from concrete_executor import FetchInventoryExecutor
from reporter import ReporterSample
from parsers.parse import parse_show_version, parse_show_inventory

logger = setup_logger("registration", Config.LEVEL)


def register_switches_from_csv(csv_path: str) -> list:
    """
    ①CSVからスイッチを仮登録する(スレッド化不要)。
    戻り値：登録したホスト名のリスト(②の収集対象を絞り込むのに使う)
    """
    registered_hosts = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            Switch.get_or_create(
                hostname=row["hostname"],
                ip_address=row["ipaddr"],
                hardware_model="unknown",
                switch_type=row["switch_type"],
                role=row["role"],
                location=row.get("location") or None,
            )
            registered_hosts.append(row["hostname"])
    logger.info(f"CSVからの仮登録が完了: {len(registered_hosts)}件")
    return registered_hosts


def collect_hardware_info(targets: list, workers: int = Config.MAX_WORKERS) -> None:
    """
    ②③実機からshow version/show inventoryを収集し、Switchレコードを更新する(スレッド化)。
    targets: SwitchListDatasetと同じ形式([{"hostname":..., "ipaddr":...}, ...])
    """
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


def main(argv):
    start = time.time()

    cur_dir = os.getcwd()
    targets_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.REGISTER_FILE)

    step = argv[0] if argv else "1"

    if step == "1":
        # ①CSV仮登録のみ
        hosts = register_switches_from_csv(targets_file)
        print(f"[INFO] 登録件数: {len(hosts)}")
        print(f"[INFO] 登録ホスト一覧(先頭10件): {hosts[:10]}")

    elif step == "2":
        print("[INFO] ステップ2(実機収集)は未実装です")
        # 後日、collect_hardware_info()をここに追加

    else:
        print("[ERROR] 引数は 1 または 2 を指定してください")
        exit(1)

    elapsed = time.time() - start
    print(f"[INFO] Elapsed: {elapsed:.2f} seconds")


if __name__ == "__main__":
    # python registration.py 1 でCSV仮登録のみ
    # python registration.py 2 で実機収集(未実装)
    main(sys.argv[1:])