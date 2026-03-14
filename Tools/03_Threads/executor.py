from abc import ABC, abstractmethod
import subprocess
import paramiko
import datetime
import time
import os
import socket
import logging
import shlex
import json
from typing import List, Type
from dataclasses import dataclass

from config import Config, setup_logger

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
# SSH Executor Interface
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
            level=self.logger.level,
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
# Example usage: main_single
#-----------------------------
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


#-------------------------------------------------
# Sample Dataset(for testing without config.ini)
#-------------------------------------------------
def sample_datasets() -> List[dict]:
    return [
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode"},
        {"ipaddr": "192.168.64.4", "hostname": "rx8node01", "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode", "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": None, "host": None},
        # Add more targets as needed
    ]

def sample_one_target() -> List[dict]:
    return [
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode", "username": Config.USERNAME, "password": Config.PASSWORD},]


#--------------------------------------------------------------
# CLI / main ( Test for single execution without threads )
#--------------------------------------------------------------
if __name__ == '__main__':

    targets = sample_one_target()
    executor = FetchLSDFExecutor
    log_level = logging.DEBUG

    main_single(_targets=targets, executor_cls=executor, level=log_level)