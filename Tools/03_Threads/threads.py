from abc import ABC, abstractmethod
import subprocess
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
# SSH Connection
# -----------------------------
class ISSHClientBase(ABC):
    def __init__(self, logger, commands: List[int], ssh_host=None, ssh_user=None):
        self.log = logger
        self.commands = commands
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user

    @abstractmethod
    def exec_command(self):
        pass


class SSHClient(ISSHClientBase):
    def exec_command(self):
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
