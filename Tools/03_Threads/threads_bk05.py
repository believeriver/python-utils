from abc import ABC, abstractmethod
import subprocess
import paramiko
import datetime
import time
import os
import sys
import socket
import logging
import queue
import threading
import json
import shlex
from typing import List, Type
from dataclasses import dataclass
import gc

from rpds.rpds import Queue


# -----------------------------
#Config
# -----------------------------
class Config(object):
    USERNAME = "root"
    PASSWORD = "rootroot"
    PORT = 22
    TIMEOUT = 10

    CONFIG_FILE = "config.ini"
    SETTINGS_DIR = "settings"
    OUTPUT_DIR = "out"
    LEVEL = logging.DEBUG
    # LEVEL = logging.INFO


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

# -----------------------------
# SSH Connection
# -----------------------------
class ISSHClientInterface(ABC):
    """SSH Client implementation using subprocess or paramiko."""
    def __init__(self,
                 commands: List[str],
                 ipaddr=None,
                 hostname=None,
                 username: str =Config.USERNAME,
                 password: str = Config.PASSWORD,
                 port: int = Config.PORT,
                 timeout: int = Config.TIMEOUT,
                 level=Config.LEVEL,):
        self.log = self._set_logger(level=level)
        self.commands = commands
        self.hostname = hostname
        self.ssh_host = ipaddr
        self.ssh_user = username
        self.password = password
        self.port = port
        self.timeout = timeout

    @staticmethod
    @abstractmethod
    def _set_logger(level):
        return setup_logger("ISSHClientInterface", level)

    @abstractmethod
    def execute_command(self):
        pass


class SSHClientSubprocess(ISSHClientInterface):
    """SSH Client implementation using subprocess"""
    @staticmethod
    def _set_logger(level):
        return setup_logger("SSHClientSubprocess", level)

    def execute_command(self):
        self.log.debug({"commands": self.commands})
        cmd = []
        if self.ssh_host:
            user_at = "{}@{}".format(self.ssh_user, self.ssh_host) if self.ssh_user else self.ssh_host
            cmd += ["ssh", user_at]

        # cmd += self.commands
        cmd += shlex.split(self.commands[0])

        self.log.debug({"commands split": cmd})
        self.log.debug("Running commands: %s", " ".join(cmd))
        try:
            p = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.timeout,)
            if p.returncode != 0:
                self.log.info("commands failed rc=%s stderr=%s", p.returncode, p.stderr.strip())
                raise RuntimeError("commands failed")
            raw_lines = [ln for ln in p.stdout.splitlines() if ln.strip()]

            # debug: raw all
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug("RAW_ALL_BEGIN total=%d", len(raw_lines))
                for ln in raw_lines:
                    self.log.debug("RAW|%s", ln)
                self.log.debug("RAW_ALL_END")
        except subprocess.TimeoutExpired as e:
            message = f"[WARN] SSH command timed out: {e.cmd} (after {e.timeout} sec)"
            self.log.error(message)
            return [message]  # or None, or 特別なオブジェクト

        except FileNotFoundError as e:
            # FileNotFoundError専用の処理
            self.log.error(f"[ERROR] Command not found: {e.filename}")
            return [f"[ERROR] Command not found: {e.filename}"]

        except Exception as e:
            # その他の例外
            self.log.error(f"[ERROR] Unexpected: {e}")
            return [f"[ERROR] {e}"]

        return raw_lines


class ParamikoSSHClient(ISSHClientInterface):
    """SSH Client implementation using Paramiko"""
    @staticmethod
    def _set_logger(level):
        return setup_logger("ParamikoSSHClient", level)

    @staticmethod
    def _recv_all(chan: paramiko.Channel, max_wait_s: float = 1.0) -> str:
        """
        簡易版: 受信が止まるまで読む（プロンプト判定なし）
        - max_wait_s: 最後の受信からこの秒数何も来なければ終了
        """
        data = bytearray()
        last_rx = time.time()

        while True:
            if chan.recv_ready():
                chunk = chan.recv(65535)
                if not chunk:
                    break
                data.extend(chunk)
                last_rx = time.time()
            else:
                if (time.time() - last_rx) >= max_wait_s:
                    break
                time.sleep(0.05)

        return data.decode("utf-8", errors="replace")

    def execute_command(self):
        self.log.debug("execute command: %s", self.commands)
        if self.ssh_host is None:
            return "[ERROR] SSH host is required (ipaddr or hostname)"

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=self.ssh_host,
                username=self.ssh_user,
                password=self.password,
                port=self.port,
                timeout=self.timeout,
                banner_timeout=30,
                auth_timeout=30,
                look_for_keys=False,
                allow_agent=False,
            )

            chan = client.invoke_shell()
            time.sleep(0.2)

            # 接続直後のバナー/プロンプト等を読み捨て（必要なら残してもOK）
            _ = self._recv_all(chan, max_wait_s=0.5)
            out_parts = []
            if self.commands:
                for cmd in self.commands:
                    if not cmd.endswith("\n"):
                        cmd += "\n"
                    chan.send(cmd)
                    # コマンド出力を収集（コマンドにより待ち時間は変わるので少し長めでもOK）
                    out_parts.append(self._recv_all(chan, max_wait_s=1.2))
            return "".join(out_parts)
            # return out_parts

        except (paramiko.SSHException,
                socket.error,
                TimeoutError) as e:
            return f"[ERROR] {self.ssh_host} : {e}"

        finally:
            try:
                client.close()
            except Exception as e:
                self.log.debug("Error during close(): %s", e)


#-----------------------------
# SSH Executor
#-----------------------------
@dataclass
class ServerInfo:
    ipaddr: str = None
    hostname: str = None
    username: str = Config.USERNAME
    password: str = Config.PASSWORD
    port: int = Config.PORT
    timeout: int = Config.TIMEOUT


class ISSHExecutorInterface(ABC):
    def __init__(self,
                 server_info: ServerInfo,
                 timeout=Config.TIMEOUT,
                 level=Config.LEVEL):
        self.server_info = server_info
        self.ssh_client_cls = self.build_ssh_client_cls()
        self.logger = setup_logger(self.name, level)
        self.commands = self.build_command()
        self.timeout = timeout
        self.result = None
        self.out_filename = self.set_out_filename(server_info.hostname, Config.OUTPUT_DIR)

    @staticmethod
    def set_out_filename(filename: str, out_dir) -> str:
        now_date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{filename}_{now_date}.txt"
        if out_dir is None:
            return filename
        else:
            filepath = os.path.join(out_dir, filename)
            return filepath

    def write_log(self):
        """
        output command results
        :return:
        """
        if self.result is None:
            self.execute_command()

        self.logger.info(f'write to {self.out_filename}')
        with open(self.out_filename, mode="w") as f:
            for text in self.result:
                text = str(text).lstrip("b'")
                text = str(text).lstrip("'")
                f.write(text + "\n")
                self.logger.debug(text)
        self.logger.info('end to write logs')

    def execute(self) -> None:
        ssh_client = self.ssh_client_cls(
            ipaddr=self.server_info.ipaddr,
            hostname=self.server_info.hostname,
            username=self.server_info.username,
            password=self.server_info.password,
            commands=self.commands,
            timeout=self.timeout,
        )
        self.result = ssh_client.execute_command()

    @staticmethod
    @abstractmethod
    def build_ssh_client_cls() -> Type[ISSHClientInterface]:
        """実行するSSHクライアントのクラスを返す
        ssh_client_cls: Type[ISSHClientInterface]
        例: return SSHClientSubprocess
        """
        pass

    @staticmethod
    @abstractmethod
    def build_command() -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute_command(self):
        pass


# -----------------------------
# Concrete Executor.
# -----------------------------
class FetchFileListExecutor(ISSHExecutorInterface):
    """
    2026.03.11 sample code for Linux command.
    SSHクライアントはSSHClientSubprocessを使用する例。
    show /home file list.
    """
    @staticmethod
    def build_ssh_client_cls():
        return SSHClientSubprocess

    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls -l /home",
        ]

    @property
    def name(self) -> str:
        return "FetchFileListExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        return self.result


class FetchLSDFExecutor(ISSHExecutorInterface):
    """
    2026.03.11 sample code for Linux command.
    show /home file list.
    show nfs volume.
    2つ以上のコマンドを実行する例。
    ParamikoSSHClient()で実行することを想定（複数コマンドの実行はsubprocessだと少し面倒なので）。
    """
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls /home --color=never",
            "df -h"
        ]

    @property
    def name(self) -> str:
        return "FetchFileListExecutor"

    def execute_command(self):
        self.execute()
        self.result = self.result.split("\n")
        self.write_log()
        # text = self.result.splitlines()
        text = self.result
        text_lines = [ln for ln in text if ln.strip()]
        result = text_lines[1:2]
        return result


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
            executor = self.executor(server_info=item, timeout=self.timeout_s)
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
                 executor_cls: Type[ISSHExecutorInterface] = FetchFileListExecutor):
    worker = ThreadWorkers(
        executor=executor_cls,
        _queue=_q,
        workers=workers,
        timeout=Config.TIMEOUT,
        level=Config.LEVEL)
    worker.run()

    print('*' * 40)
    print(json.dumps(worker.results, indent=2, ensure_ascii=False))


def main_single(_targets: List[dict],
                executor_cls: Type[ISSHExecutorInterface] = FetchFileListExecutor):
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
        executor = executor_cls(server_info=dataset)
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
    log_level = logging.WARNING
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
        if a == "--threaded":
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
    else:
        if threaded:
            # THREADING version
            q = set_queue(_targets=targets)
            main_threads(_q=q, workers=3, executor_cls=executor)
        else:
            # NO threading version
            main_single(_targets=targets, executor_cls=executor)


if __name__ == "__main__":
    main(sys.argv[1:])

    gc.collect()