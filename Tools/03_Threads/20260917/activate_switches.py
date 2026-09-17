# activate_switches.py（新規、プロジェクト直下）
"""
CSVに列挙されたホスト名のスイッチを一括で有効化するスクリプト。
実行例: python activate_switches.py settings/activate_list.csv
"""

import sys
import csv

from config import Config, setup_logger
from models.switch import Switch

logger = setup_logger("activate_switches", Config.LEVEL)


def activate_from_csv(csv_path: str) -> None:
    success, failed = [], []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        for row in reader:
            hostname = (row.get("hostname") or "").strip()
            if not hostname:
                continue
            if Switch.activate(hostname):
                success.append(hostname)
            else:
                failed.append(hostname)

    print("=" * 60)
    print(f"[INFO] 有効化成功: {len(success)}件")
    print(f"[INFO] 有効化失敗(DB未登録): {len(failed)}件")
    if failed:
        for h in failed:
            print(f"  - {h}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] CSVファイルのパスを指定してください")
        exit(1)
    activate_from_csv(sys.argv[1])