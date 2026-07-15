import logging
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # config.pyがあるフォルダ = プロジェクトルート
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)                        # 初回起動時にdataフォルダがなければ作成

DB_PATH = DATA_DIR / "network_monitor.db"


# -----------------------------
#Config
# -----------------------------
class Config(object):
    # SSH Connection Settings
    USERNAME = "root"
    PASSWORD = "rootroot"
    PORT = 22
    TIMEOUT = 10

    # Other Settings
    CONFIG_FILE = "config.ini"
    REGISTER_FILE = "register.ini"
    SETTINGS_DIR = "settings"
    OUTPUT_DIR = "out"
    LEVEL = logging.WARN

    # SET EXECUTOR_CLS
    executor_class_list = [
        "FetchFileListExecutor",
        "FetchLSDFExecutor",
        "FetchPWDExecutor",
        "FetchInventoryExecutor",
    ]

    reporter_class_list = [
        "ReporterSample",]

    # SELECT EXECUTOR AND REPORTER
    executor_idx = 2
    reporter_idx = 0

    EXECUTOR_CLS = executor_class_list[executor_idx]
    REPORTER_CLS = reporter_class_list[reporter_idx]

    # THREADING
    MAX_WORKERS = 3

    # DATABASE
    DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
    EXECUTOR_TO_SAVER = {
        "FetchMacTableExecutor": "MacAddressDBSaver",
        "FetchCdpExecutor": "CdpNeighborDBSaver",
        "FetchArpExecutor": "ArpDBSaver",
        "FetchInventoryExecutor": "InventoryDBSaver",
    }

    # SNMP
    # Switchテーブルに登録済みの、実際のホスト名と完全に一致させる必要があります。
    # 今回のテスト環境であればrx8headnode（コアスイッチとして動かしているマシン）です。
    CORE_SWITCHES = [
        {"hostname": "rx8headnode", "host": "192.168.64.2", "community": "public"},
        # 実際のコアスイッチが複数台あれば、同じ形式で追加
        # {"hostname": "core-sw02", "host": "192.168.0.2", "community": "public"},
    ]



# -----------------------------
# Logger
# -----------------------------
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(threadName)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger