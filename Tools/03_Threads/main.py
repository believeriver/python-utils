from abc import ABC, abstractmethod
import datetime
import os
import sys
import logging
import queue
import threading
import json
from typing import List, Type
from pprint import pformat
import gc

from rpds.rpds import Queue

from config import Config, setup_logger
from utils import SwitchListDataset, IReporterInterface, ReporterSample
from executor import (
    ISSHExecutorInterface,
    FetchFileListExecutor,
    FetchLSDFExecutor,
    ServerInfo,
    main_single,
)


#-----------------------------
# Thread Worker
#-----------------------------
class IThreadWorkerInterface(ABC):
    def __init__(self,
                 executor: Type[ISSHExecutorInterface],
                 _queue, workers=1, timeout=Config.TIMEOUT, level=Config.LEVEL):
        self.executor = executor
        self.queue = _queue
        self.workers = workers
        self.timeout_s = timeout
        self.logger = setup_logger(self.name, level)
        self.result_lock = threading.Lock()
        self.results = []

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def worker(self):
        pass


class ThreadWorkers(IThreadWorkerInterface):
    """
    QueueからServerInfoを取り出し、SSH Executorを実行するスレッドワーカーの例。
     - executor: ISSHExecutorInterfaceを継承したクラスを指定
     - _queue: ServerInfoオブジェクトを入れたQueueを指定
     - workers: スレッド数
     - timeout: SSHコマンドのタイムアウト秒数
     - level: ログレベル
     - 結果はself.resultsに格納（必要に応じてロックを使用して安全にアクセス）
     - 結果の格納方法は必要に応じて変更してください（例: self.results.append((server_info, res))など）
     - ログにはスレッド名も含まれるので、どのスレッドがどのサーバーを処理しているかがわかるようになっています。
     - 例: ThreadWorkers(executor=FetchLSDFExecutor, _queue=q, workers=5, timeout=10, level=logging.DEBUG).run()
     - 例: ThreadWorkers(executor=FetchFileListExecutor, _queue=q, workers=5, timeout=10, level=logging.DEBUG).run()
    """
    @property
    def name(self) -> str:
        return "ThreadWorkers"

    def run(self):
        ts = []
        for _ in range(self.workers):
            t = threading.Thread(target=self.worker)
            t.start()
            ts.append(t)
        [self.queue.put(None) for _ in range(len(ts))]
        [t.join() for t in ts]

    def worker(self):
        self.logger.debug('workers start')
        while True:
            item = self.queue.get()
            if item is None:
                break
            self.logger.info({'thread': (item.hostname, item.ipaddr)})
            executor = self.executor(server_info=item, timeout=self.timeout_s, level=self.logger.level)
            res = executor.execute_command()
            messages = {item.hostname: res}
            self.logger.info(f"done: {messages}")
            # self.logger.info(f"done:\n{pformat(messages, indent=2)}")

            with self.result_lock:
                self.results.append({item.hostname: res})

            self.logger.debug(type(res))
            if type(res) == list:
                self.logger.debug(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                self.logger.debug(res)
            self.queue.task_done()
        self.logger.debug('workers end')


#-----------------------------
# Set Queue
#-----------------------------
def set_queue(_targets: List[dict]):
    q = queue.Queue()
    for t in _targets:
        server_info = ServerInfo(
            ipaddr=t.get("ipaddr", None),
            hostname=t.get("hostname", None),
            username=t.get("username", Config.USERNAME),
            password=t.get("password", Config.PASSWORD))
        q.put(server_info)
    return q


#-----------------------------
# Main
#-----------------------------
def main_threads(_q: Queue,
                 workers=1,
                 executor_cls: Type[ISSHExecutorInterface] = FetchFileListExecutor,
                 reporter_cls: Type[IReporterInterface] = ReporterSample,
                 level=Config.LEVEL):
    worker = ThreadWorkers(
        executor=executor_cls,
        _queue=_q,
        workers=workers,
        timeout=Config.TIMEOUT,
        level=level)
    worker.run()

    reporter_cls.print_results(worker.results)


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
    main(sys.argv[1:])

    gc.collect()