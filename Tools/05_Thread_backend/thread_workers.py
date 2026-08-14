# thread_workers.py
from abc import ABC, abstractmethod
import queue
import threading
import json
from typing import List, Type

from config import Config, setup_logger
from utils import IReporterInterface, ReporterSample
from executor import ISSHExecutorInterface, ServerInfo


#-----------------------------
# Thread Worker
#-----------------------------
class IThreadWorkerInterface(ABC):
    def __init__(self,
                 executor: Type[ISSHExecutorInterface],
                 _queue: queue.Queue, workers=1, timeout=Config.TIMEOUT, level=Config.LEVEL):
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
     - 例: ThreadWorkers(executor=FetchLSDFExecutor, _queue=q, workers=5, timeout=10, level=logging.DEBUG).run()
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
            self.logger.info({'thread': (item.hostname, item.ipaddr, item.username, item.password)})
            executor = self.executor(server_info=item, timeout=self.timeout_s, level=self.logger.level)
            res = executor.execute_command()
            messages = {item.hostname: res}
            self.logger.info(f"done: {messages}")

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
def set_queue(_targets: List[dict]) -> queue.Queue:
    q = queue.Queue()
    for t in _targets:
        username = t.get("username", Config.USERNAME)
        if username == "" or username is None:
            username = Config.USERNAME
        password = t.get("password", Config.PASSWORD)
        if password == "" or password is None:
            password = Config.PASSWORD

        server_info = ServerInfo(
            ipaddr=t.get("ipaddr", None),
            hostname=t.get("hostname", None),
            username=username,
            password=password,)
        q.put(server_info)
    return q


#-----------------------------
# Run
#-----------------------------
def main_threads(_q: queue.Queue,
                 workers=1,
                 executor_cls: Type[ISSHExecutorInterface] = None,
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
    return worker.results