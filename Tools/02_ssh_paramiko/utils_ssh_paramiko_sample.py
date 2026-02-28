from abc import ABC, abstractmethod
import paramiko
import subprocess
import time
import os
import logging
import json
import gc


#-----------------------
# Logger
#-----------------------
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


#-----------------------
# SSH Client Interface
#-----------------------
class SSHClientInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute_command(self, command: str) -> str:
        pass

    @abstractmethod
    def close(self):
        pass

#-----------------------
# Paramiko SSH Client Implementation
#-----------------------
class ParamikoSSHClient(SSHClientInterface):
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.logger = setup_logger("ParamikoSSHClient")

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.logger.info(f"Connected to {self.hostname}")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.hostname}: {e}")
            raise

    def execute_command(self, command: str) -> str:
        if not self.client:
            raise Exception("SSH client is not connected.")

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                self.logger.error(f"Error executing command '{command}': {error}")
                return error
            return output
        except Exception as e:
            self.logger.error(f"Failed to execute command '{command}': {e}")
            raise

    def close(self):
        if self.client:
            self.client.close()
            self.logger.info(f"Connection to {self.hostname} closed.")



