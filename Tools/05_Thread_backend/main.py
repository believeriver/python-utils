import datetime
import os
import sys
import logging
import time
from pprint import pformat
import gc

from config import Config, setup_logger
from thread_workers import set_queue, main_threads, main_single
from dataset import *
from reporter import *
from concrete_executor import *


# -----------------------------
# CLI / main
# -----------------------------
def parse_args(argv):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_level = Config.LEVEL
    debug = False
    info = False
    threaded = False

    print(f"[INFO] {today}")
    if len(argv) == 0:
        print("[ERROR]Please input option (number, log level)")
        print("[INFO]Example: python main.py 1 -> Check Config.EXECUTOR_CLS")
        print("[INFO]Example: python main.py 2 -> Run SSH Executor")
        print("[INFO]Example: python main.py 2 -t -> Run SSH Executor with threading")
        print("[INFO]Example: python main.py 2 --debug -> Run SSH Executor with DEBUG log level")
        exit(1)

    target = argv[0]
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--debug":
            log_level = logging.DEBUG
            debug = True
            i += 1
            continue
        if a == "--info":
            log_level = logging.INFO
            info = True
            i += 1
            continue
        if a == "-t" or a == "--threaded":
            threaded = True
        i += 1
    return int(target), log_level, debug, info, threaded


def main(argv):
    # targets from config.ini
    main_logger = setup_logger("main", Config.LEVEL)

    module = sys.modules[__name__]
    dataset_cls = getattr(module, Config.DATASET_CLS, None)

    if dataset_cls is None:
        print(f"[ERROR] Dataset class '{Config.DATASET_CLS}' not found.")
        exit(1)
    if dataset_cls == ClusterIniDataset:
        _dataset = dataset_cls(Config.SETTINGS_DIR, Config.CLUSTER_INI_FILE)
    else:
        _dataset = dataset_cls(Config.SETTINGS_DIR, Config.CONFIG_FILE)
    main_logger.debug(_dataset)
    targets = _dataset.targets_list

    target, log_level, debug, info, threaded = parse_args(argv)
    _executor = None
    _reporter = None
    print(f"[INFO] Target: {target}, Log Level: {logging.getLevelName(log_level)}, Threaded: {threaded}")
    if target == 1:
        print("[INFO] Checking EXECUTOR_CLS...")
        print(f"[INFO] EXECUTOR_CLS: {Config.EXECUTOR_CLS}")
        print(f"[INFO] REPORTER_CLS: {Config.REPORTER_CLS}")
        print(f"[INFO] DATASET_CLS: {Config.DATASET_CLS}")
        if Config.EXECUTOR_CLS == "ClusterCommandExecutor":
            # If using ClusterCommandExecutor, set a longer timeout
            Config.TIMEOUT = Config.CLUSTER_COMMAND_TIMEOUT
            print(f"[INFO] Using ClusterCommandExecutor, setting TIMEOUT to {Config.TIMEOUT} seconds.")

    if target == 2:
        # executor = FetchLSDFExecutor
        executor_name = Config.EXECUTOR_CLS
        reporter_cls = Config.REPORTER_CLS
        _executor = getattr(module, executor_name, None)
        _reporter = getattr(module, reporter_cls, None)

    if _executor is None:
        print("[ERROR]Please input option (number, log level): number 1 or 2")
        exit(1)

    if threaded:
        # THREADING version
        q = set_queue(_targets=targets)
        main_threads(_q=q,
                     workers=Config.MAX_WORKERS,
                     executor_cls=_executor,
                     reporter_cls=_reporter,
                     timeout=Config.TIMEOUT,
                     level=log_level)
    else:
        # NO threading version
        main_single(_targets=targets, executor_cls=_executor, level=log_level)


if __name__ == "__main__":
    dt_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    start = time.time()
    main(sys.argv[1:])
    end = time.time()
    print(f"[INFO] Start: {dt_now}, Elapsed Time: {end - start:.2f} seconds")

    gc.collect()