import datetime
import os
import sys
import logging
import time
from pprint import pformat
import gc

from config import Config, setup_logger
from utils import SwitchListDataset, IReporterInterface, ReporterSample
from executor import (
    ISSHExecutorInterface,
    FetchFileListExecutor,
    FetchLSDFExecutor,
    ServerInfo,
    main_single,
)
from concrete_executor import FetchPWDExecutor, PacctExecutor
from thread_workers import set_queue, main_threads


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
    dataset = SwitchListDataset()
    main_logger.debug(dataset)
    targets = dataset.targets_list

    target, log_level, debug, info, threaded = parse_args(argv)
    executor = None
    reporter = None
    print(f"[INFO] Target: {target}, Log Level: {logging.getLevelName(log_level)}, Threaded: {threaded}")
    if target == 1:
        print("[INFO] Checking EXECUTOR_CLS...")
        print(f"[INFO] EXECUTOR_CLS: {Config.EXECUTOR_CLS}")
        print(f"[INFO] REPORTER_CLS: {Config.REPORTER_CLS}")
    if target == 2:
        # executor = FetchLSDFExecutor
        executor_name = Config.EXECUTOR_CLS
        reporter_cls = Config.REPORTER_CLS
        module = sys.modules[__name__]
        executor = getattr(module, executor_name, None)
        reporter = getattr(module, reporter_cls, None)

    if executor is None:
        print("[ERROR]Please input option (number, log level): number 1 or 2")
        exit(1)

    if threaded:
        # THREADING version
        q = set_queue(_targets=targets)
        main_threads(_q=q,
                     workers=Config.MAX_WORKERS,
                     executor_cls=executor,
                     reporter_cls=reporter,
                     level=log_level)
    else:
        # NO threading version
        main_single(_targets=targets, executor_cls=executor, level=log_level)


if __name__ == "__main__":
    dt_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    start = time.time()
    main(sys.argv[1:])
    end = time.time()
    print(f"[INFO] Start: {dt_now}, Elapsed Time: {end - start:.2f} seconds")

    gc.collect()