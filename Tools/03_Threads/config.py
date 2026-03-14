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
    SETTINGS_DIR = "settings"
    OUTPUT_DIR = "out"
    LEVEL = logging.WARN

    # SET EXECUTOR_CLS
    executor_class_list = [
        "FetchFileListExecutor",
        "FetchLSDFExecutor",]
    reporter_class_list = [
        "ReporterSample",]

    executor_idx = 1
    reporter_idx = 0

    EXECUTOR_CLS = executor_class_list[executor_idx]
    REPORTER_CLS = reporter_class_list[reporter_idx]

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