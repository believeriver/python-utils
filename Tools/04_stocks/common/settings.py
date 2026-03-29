import os
import sys
import logging

path_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path_dir)

USER_AGENT = '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0'

LOG_FILE = path_dir + '/scraping.log'
LOG_LEVEL = logging.INFO


# -----------------------------
# Logger
# -----------------------------
def setup_logger(name, level=LOG_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(threadName)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger

