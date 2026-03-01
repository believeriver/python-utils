"""
Description:
    SSH-based log collection tool for network devices and Linux hosts.

    This script connects to one or more targets over SSH (via Paramiko),
    runs a predefined set of commands (Executor), writes the command output
    to timestamped log files, and prints a JSON-formatted execution summary.

    Targets are loaded from a simple CSV-style config file:
        settings/config.ini  (one line per target: "hostname,ipaddr")

    Key components:
      - ParamikoSSHClient: minimal interactive-shell SSH runner (invoke_shell)
      - ExecutorInterface: defines a command set per task (e.g., file list, pwd)
      - FetchLogFactory: orchestrates execution across all targets and builds a summary

    Usage:
        python <script_name>.py <target> [--debug|--info]

        target:
            1 = FetchFileListExecutor  (e.g., "ls -l /home --color=never", "df -h")
            2 = FetchPwdExecutor       (e.g., "pwd")

    Output:
        - Per-target log file under ./out/
        - JSON summary printed to stdout/log

Author:
    Nobuyuki Tagawa

Version:
    1.0.0  (2026-02-28)
"""
from abc import ABC, abstractmethod
import paramiko
import subprocess
import datetime
import time
import os
import sys
import socket
import logging
import json
from typing import List, Type
import gc


# -----------------------------
#Config
# -----------------------------
class Config(object):
    USERNAME = "root"
    PASSWORD = "rootroot"
    PORT = 22

    CONFIG_FILE = "config.ini"
    SETTINGS_DIR = "settings"
    OUTPUT_DIR = "out"
    # LEVEL = logging.DEBUG
    LEVEL = logging.INFO


# -----------------------------
# Logger
# -----------------------------
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


# -----------------------------
# SSH Client Interface
# -----------------------------
class SSHClientInterface(ABC):
    @abstractmethod
    def execute_command(self) -> str:
        pass


# -----------------------------
# Paramiko SSH Client Implementation
# -----------------------------
class ParamikoSSHClient(SSHClientInterface):
    def __init__(self,
                 ip: str,
                 username: str,
                 password: str,
                 port: int = 22,
                 commands:  List[str] = None,
                 level=logging.INFO):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.commands = commands
        self.logger = setup_logger("ParamikoSSHClient", level)

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
        self.logger.debug("execute command: %s", self.commands)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                self.ip,
                username=self.username,
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
            return f"[ERROR] {self.ip} : {e}"

        finally:
            try:
                client.close()
            except Exception as e:
                self.logger.debug("Error during close(): %s", e)


# -----------------------------
# Executor
# -----------------------------
class ExecutorInterface(ABC):
    def __init__(self,
                 ip: str,
                 username: str,
                 password: str,
                 port: int = 22,
                 filename: str = 'hostname',
                 out_dir: str = None,
                 level = logging.INFO,
                 ):
        self.commands = self.build_command()
        self.filename = filename
        self.out_filename = self.set_out_filename(self.filename, out_dir)
        self.logger = setup_logger(self.name, level=level)
        self.results = None
        self.ssh_client = ParamikoSSHClient(
            ip = ip,
            username = username,
            password = password,
            port = port,
            commands=self.commands,
            level=level,
        )

    @staticmethod
    @abstractmethod
    def build_command() -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

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
        if self.results is None:
            self.run()

        self.logger.info(f'write to {self.out_filename}')
        with open(self.out_filename, mode="w") as f:
            for text in self.results:
                text = str(text).lstrip("b'")
                text = str(text).lstrip("'")
                f.write(text + "\n")
                self.logger.debug(text)
        self.logger.info('end to write logs')

    def run(self) -> None:
        self.results = self.ssh_client.execute_command().split("\n")


# -----------------------------
# Concrete Executor.
# -----------------------------
class FetchFileListExecutor(ExecutorInterface):
    """
    2026.03.01 sample code for Linux command.
    show /home file list.
    show nfs volume.
    """
    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls -l /home --color=never",
            "df -h"
        ]

    @property
    def name(self) -> str:
        return "FetchFileListExecutor"


class FetchPwdExecutor(ExecutorInterface):
    """
    2026.03.01 sample code for Linux command.
    show current directory.
    """
    @staticmethod
    def build_command() -> List[str]:
        return [
            "pwd",
        ]

    @property
    def name(self) -> str:
        return "FetchPwdExecutor"


# -----------------------------
# Utils
# -----------------------------
class SwitchListDataset(object):
    """
    fetch ip address and hostname list from config life.
    """
    def __init__(self, config_file :str):
        self.config_file = config_file
        self.hostname_list = []
        self.ipaddr_list = []
        self.import_config()

    def import_config(self):
        with open(self.config_file, mode="r") as f:
            items = f.read().splitlines()

        for item in items:
            hostname, ipaddr = item.split(",")
            self.hostname_list.append(hostname)
            self.ipaddr_list.append(ipaddr)

    def __str__(self):
        for cnt in range(len(self.hostname_list)):
            print(f' --- {cnt} ---')
            print(f'hostname : {self.hostname_list[cnt]}')
            print(f'ipaddr   : {self.ipaddr_list[cnt]}')
        return 'end of SwitchConfigList'


# -----------------------------
# Orchestrator
# -----------------------------
class FetchLogFactory(object):
    def __init__(self,
                 dataset_cls: Type[SwitchListDataset],
                 executor_cls: Type[ExecutorInterface]):
        self.dataset_cls = dataset_cls
        self.executor_cls = executor_cls
        self.username = Config.USERNAME
        self.password = Config.PASSWORD
        self.port = Config.PORT
        self.level = Config.LEVEL
        self.logger = setup_logger(self.name, level=self.level)
        self.config_file = None
        self.output_dir = None
        self.create_file_path()
        self.summary = []

    def create_file_path(self):
        cur_dir = os.getcwd()
        self.config_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.CONFIG_FILE)
        self. output_dir = os.path.join(cur_dir, Config.OUTPUT_DIR)
        self.logger.debug(f"config file: {self.config_file}")
        self.logger.debug(f"output_dir: {self.output_dir}")

    @property
    def name(self) -> str:
        """
        The method for generating the summary can be freely customized by overriding it.
        :return: None
        """
        return 'FetchLogFactory'

    def fetch_summary(self, hostname: str, ipaddr: str, command_result: List[str]):
        """
        The method for generating the summary can be freely customized by overriding it.
        :return: None
        """
        result = dict()
        result['HOSTNAME'] = hostname
        result['IPADDR'] = ipaddr
        texts = []
        for text in command_result:
            text = str(text).lstrip("b'")
            text = str(text).lstrip("'")
            self.logger.debug(text)
            texts.append(text)
        result['COMMAND_RESULT'] = texts
        self.summary.append(result)

    def print_summary(self):
        """
        The method for generating the summary can be freely customized by overriding it.
        :return: None
        """
        # for item in self.summary:
        #     print(",".join(str(x) for x in item))
        self.logger.info(json.dumps(self.summary, indent=2, ensure_ascii=False))

    def fetch_log_from_targets(self):
        dataset = self.dataset_cls(self.config_file)
        self.logger.info("Start fetch log from dataset in FetchLogs")
        for cnt in range(len(dataset.ipaddr_list)):
            self.logger.info(f' --- {cnt} ---')
            self.logger.info(f'hostname : {dataset.hostname_list[cnt]}')
            self.logger.info(f'ipaddr   : {dataset.ipaddr_list[cnt]}')
            executor_cls = self.executor_cls(
                ip=dataset.ipaddr_list[cnt],
                username=self.username, password=self.password, port=self.port,
                filename=dataset.hostname_list[cnt],out_dir=self.output_dir,
                level=self.level)
            executor_cls.run()
            executor_cls.write_log()
            self.fetch_summary(hostname=dataset.hostname_list[cnt],
                               ipaddr=dataset.ipaddr_list[cnt],
                               command_result=executor_cls.results)

    def run(self):
        self.fetch_log_from_targets()
        self.logger.info("Finish fetch log from targets in FetchLogs")
        self.print_summary()


# -----------------------------
# CLI / main
# -----------------------------
def parse_args(argv):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_level = logging.WARNING
    debug = False
    info = False

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
        i += 1
    return int(target), log_level, debug, info


def main_cls(factory_cls: Type[FetchLogFactory], executor_cls: Type[ExecutorInterface]):
    dataset_cls = SwitchListDataset
    executor_factory = factory_cls(dataset_cls, executor_cls)
    executor_factory.run()


def main(argv=None):
    target, log_level, debug, info = parse_args(argv)
    factory = FetchLogFactory
    executor = None
    if target == 1:
        executor = FetchFileListExecutor
    if target == 2:
        executor = FetchPwdExecutor

    if executor is None:
        exit(1)
    else:
        main_cls(factory, executor)


if __name__ == '__main__':
    # print(sys.argv)
    main(sys.argv[1:])

    gc.collect()

