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
    TIMEOUT = 30

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
                 hostname=None,
                 username=None,
                 password: str = None,
                 port: int = 22,
                 level=Config.LEVEL,):
        self.log = self._set_logger(level=level)
        self.commands = commands
        self.ssh_host = hostname
        self.ssh_user = username
        self.password = password
        self.port = port

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
        cmd += self.commands

        self.log.debug("Running commands: %s", " ".join(cmd))
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
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

    def execute_command(self) -> str:
        self.log.debug("execute command: %s", self.commands)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=self.ssh_host,
                username=self.ssh_user,
                password=self.password,
                port=self.port,
                timeout=30,
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

        except (paramiko.SSHException, socket.gaierror, TimeoutError) as e:
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
    hostname: str = None
    username: str = Config.USERNAME
    password: str = Config.PASSWORD
    port: int = Config.PORT
    timeout: int = Config.TIMEOUT


class ISSHExecutorInterface(ABC):
    def __init__(self,
                 ssh_client_cls: Type[ISSHClientInterface],
                 server_info: ServerInfo,
                 level=Config.LEVEL):
        self.server_info = server_info
        self.ssh_client_cls = ssh_client_cls
        self.logger = setup_logger(self.name, level)
        self.commands = self.build_command()

    def execute(self):
        ssh_client = self.ssh_client_cls(
            hostname=self.server_info.hostname,
            username=self.server_info.username,
            password=self.server_info.password,
            commands=self.commands,
        )
        return ssh_client.execute_command()

    @staticmethod
    @abstractmethod
    def build_command() -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# -----------------------------
# Concrete Executor.
# -----------------------------
class FetchFileListExecutor(ISSHExecutorInterface):
    """
    2026.03.01 sample code for Linux command.
    show /home file list.
    """
    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls -l /home --color=never",
        ]

    @property
    def name(self) -> str:
        return "FetchFileListExecutor"


class FetchLSDFExecutor(ISSHExecutorInterface):
    """
    2026.03.01 sample code for Linux command.
    show /home file list.
    show nfs volume.
    2つ以上のコマンドを実行する例。
    ParamikoSSHClient()で実行することを想定（複数コマンドの実行はsubprocessだと少し面倒なので）。
    """
    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls /home --color=never",
            "df -h"
        ]

    @property
    def name(self) -> str:
        return "FetchFileListExecutor"


#-----------------------------
# Thread Worker
#-----------------------------
class IThreadWorkerInterface(ABC):
    def __init__(self,
                 ssh_client_cls: Type[ISSHClientInterface],
                 executor: Type[ISSHExecutorInterface],
                 _queue, workers=1, timeout=10, level=Config.LEVEL):
        self.ssh_client_cls = ssh_client_cls
        self.executor = executor
        self.queue = _queue
        self.workers = workers
        self.timeout_s = timeout
        self.logger = setup_logger(self.name, level)

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

    @abstractmethod
    def worker(self):
        self.logger.info('workers start')
        while True:
            item = self.queue.get()
            if item is None:
                break
            self.logger.info({'thread': item})
            executor = self.executor(ssh_client_cls=self.ssh_client_cls, server_info=item)
            executor.execute()
            self.queue.task_done()
        self.logger.info('workers end')


#-----------------------------
# Main
#-----------------------------
def main():
    # Load config (if needed)
    # config = ConfigLoader.load(Config.CONFIG_FILE)

    targets = [
        {"host": "192.168.64.2", "user": Config.USERNAME, "password": Config.PASSWORD},
        {"host": "192.168.64.2", "user": Config.USERNAME, "password": Config.PASSWORD},
        {"host": "192.168.64.2", "user": Config.USERNAME, "password": Config.PASSWORD},
        # Add more targets as needed
    ]

    datasets = []
    for t in targets:
        server_info = ServerInfo(hostname=t.get("host", ""), username=t.get("user", ""), password=t.get("password", ""))
        datasets.append(server_info)

    print(datasets)

    executor1 = FetchFileListExecutor(ssh_client_cls=SSHClientSubprocess, server_info=datasets[0],level=Config.LEVEL)
    executor2 = FetchLSDFExecutor(ssh_client_cls=ParamikoSSHClient, server_info=datasets[1],level=Config.LEVEL)

    results_1 = executor1.execute()
    results_2 = executor2.execute()

    print('-' * 40)
    print('1', results_1)
    print('-' * 40)
    print('2', results_2)


if __name__ == "__main__":
    main()