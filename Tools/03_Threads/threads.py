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
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger

# -----------------------------
# SSH Connection
# -----------------------------
class ISSHClientInterface(ABC):
    """SSH Client implementation using subprocess or paramiko."""
    def __init__(self, logger, commands: List[str], ssh_host=None, ssh_user=None):
        self.log = logger
        self.commands = commands
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user

    @abstractmethod
    def execute_command(self):
        pass


class SSHClient(ISSHClientInterface):
    """SSH Client implementation using subprocess"""
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
    def __init__(self,
                 host: str,
                 username: str,
                 password: str,
                 port: int = 22,
                 commands:  List[str] = None,
                 level=logging.INFO):
        super().__init__(
            logger=setup_logger("ParamikoSSHClient", level),
            commands=commands,
            ssh_host=host,
            ssh_user=username)
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
                self.logger.debug("Error during close(): %s", e)

