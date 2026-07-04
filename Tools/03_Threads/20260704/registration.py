# registration.py
import csv
from models.switch import Switch


def register_switches_from_csv(csv_path: str) -> None:
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            Switch.get_or_create(
                hostname=row["hostname"],
                ip_address=row["ip_address"],
                hardware_model="unknown",   # ②で上書きされる仮値
                switch_type=row["switch_type"],
                role=row["role"],
                location=row.get("location") or None,
            )
    print("[INFO] CSVからの仮登録が完了しました")
