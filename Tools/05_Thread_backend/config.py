import logging


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
    CLUSTER_INI_FILE = "cluster.ini"
    SETTINGS_DIR = "settings"
    OUTPUT_DIR = "out"
    LEVEL = logging.WARN

    # SELECT EXECUTOR, REPORTER, DATASET
    executor_idx = 3
    reporter_idx = 0
    dataset_idx = 0

    # SET EXECUTOR_CLS
    executor_class_list = [
        "FetchFileListExecutor",
        "FetchLSDFExecutor",
        "FetchPWDExecutor",
        "ClusterCommandExecutor",
    ]
    reporter_class_list = [
        "ReporterSample",
    ]
    dataset_class_list = [
        "ClusterIniDataset" ,
        "SwitchListDataset",
    ]

    EXECUTOR_CLS = executor_class_list[executor_idx]
    REPORTER_CLS = reporter_class_list[reporter_idx]
    DATASET_CLS = dataset_class_list[dataset_idx]

    # THREADING
    MAX_WORKERS = 3


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