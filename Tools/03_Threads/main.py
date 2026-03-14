from abc import ABC, abstractmethod
import datetime
import os
import sys
import logging
import queue
import threading
import json
from typing import List, Type
import gc

from rpds.rpds import Queue

from config import Config, setup_logger
from executor import (
    ISSHExecutorInterface,
    FetchFileListExecutor,
    FetchLSDFExecutor,
    ServerInfo,)


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
        self.logger.info('workers start')
        while True:
            item = self.queue.get()
            if item is None:
                break
            self.logger.info({'thread': item})
            executor = self.executor(server_info=item, timeout=self.timeout_s, level=self.logger.level)
            res = executor.execute_command()

            with self.result_lock:
                self.results.append({item.hostname: res})

            self.logger.debug(type(res))
            if type(res) == list:
                self.logger.info(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                self.logger.info(res)
            self.queue.task_done()
        self.logger.info('workers end')


# -----------------------------
# Utils
# -----------------------------
class SwitchListDataset(object):
    """
    fetch ip address and hostname list from config life.
        - config.iniの内容を読み込んで、IPアドレスとホスト名のリストを作成する例。
        - config.iniは以下のような形式を想定（1行目がヘッダー、2行目以降がデータ）：
        ipaddr,host,user,password
    folder: settings
    file: config.ini
    """
    def __init__(self):
        cur_dir = os.getcwd()
        self.targets_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.CONFIG_FILE)
        self.targets_list = []
        self.import_config()

    def import_config(self):
        with open(self.targets_file, 'r', encoding="utf-8") as f:
            headers = []
            lines = f.readlines()
            for cnt, line in enumerate(lines):
                device = {}
                line = line.rstrip("\n")
                items = line.split(",")
                if cnt == 0:
                    for item in items:
                        headers.append(item)
                else:
                    for idx, item in enumerate(items):
                        if item == "":
                            item = None
                        device[headers[idx]] = item
                if not line:
                    continue
                if device != {}:
                    self.targets_list.append(device)

    def __str__(self):
        return json.dumps(self.targets_list, indent=2, ensure_ascii=False)


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
                 level=Config.LEVEL):
    worker = ThreadWorkers(
        executor=executor_cls,
        _queue=_q,
        workers=workers,
        timeout=Config.TIMEOUT,
        level=level)
    worker.run()

    print('*' * 40)
    print(json.dumps(worker.results, indent=2, ensure_ascii=False))


def main_single(_targets: List[dict],
                executor_cls: Type[ISSHExecutorInterface] = FetchFileListExecutor,
                level=Config.LEVEL):
    datasets = []
    for t in _targets:
        server_info = ServerInfo(
            ipaddr=t.get("ipaddr", None),
            hostname=t.get("hostname", None),
            username=t.get("username", Config.USERNAME),
            password=t.get("password", Config.PASSWORD))
        datasets.append(server_info)

    print(len(datasets))
    results = []
    for dataset in datasets:
        executor = executor_cls(server_info=dataset, level=level)
        res = executor.execute_command()
        results.append({dataset.hostname: res})

    print(json.dumps(results, indent=2, ensure_ascii=False))


#-----------------------------
# Sample Dataset(for testing without config.ini)
#-----------------------------
def sample_dataset() -> List[dict]:
    return [
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode"},
        {"ipaddr": "192.168.64.4", "hostname": "rx8node01", "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode", "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": None, "host": None},
        # Add more targets as needed
    ]


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
        print("Please input option (number, log level)")
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

    # targets from sample dataset (for testing without config.ini)
    # targets = sample_dataset()

    target, log_level, debug, info, threaded = parse_args(argv)
    executor = None
    if target == 1:
        executor = FetchFileListExecutor
    if target == 2:
        executor = FetchLSDFExecutor

    if executor is None:
        exit(1)

    if threaded:
        # THREADING version
        q = set_queue(_targets=targets)
        main_threads(_q=q, workers=3, executor_cls=executor, level=log_level)
    else:
        # NO threading version
        main_single(_targets=targets, executor_cls=executor, level=log_level)


if __name__ == "__main__":
    main(sys.argv[1:])

    gc.collect()