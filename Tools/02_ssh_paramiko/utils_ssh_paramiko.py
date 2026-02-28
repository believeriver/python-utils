from abc import ABC, abstractmethod
import paramiko
import subprocess
import datetime
import time
import os
import logging
import json
from typing import List, Sequence
import gc


#-----------------------
#Config
#-----------------------

class Config(object):
    USERNAME = "root"
    PASSWORD = "rootroot"
    PORT = 22
    LEVEL = logging.DEBUG


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
    def execute_command(self) -> str:
        pass

#-----------------------
# Paramiko SSH Client Implementation
#-----------------------
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

    def execute_command(self) -> str:
        execute_result = None
        self.logger.debug(f"--- execute command: {self.commands}")
        try:
            with (paramiko.SSHClient() as client):
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
                client.connect(
                    self.ip,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    timeout=30,
                )
                remote_shell = client.invoke_shell()
                time.sleep(2)


                execute_result = remote_shell.recv(655535).decode("utf-8", errors="replace")
                if self.commands != [] and self.commands is not None:
                    for command in self.commands:
                        if not command.endswith("\n"):
                            command = command + "\n"
                        remote_shell.send(command)
                    time.sleep(3)
                execute_result = remote_shell.recv(655535).decode("utf-8", errors="replace")
        except paramiko.SSHException as e:
            execute_result = f"[ERROR] {self.ip} : {str(e)}"
        return execute_result


#---------------
# Executor
#---------------
class ExecutorInterface(ABC):
    def __init__(self,
                 ip: str,
                 username: str,
                 password: str,
                 port: int = 22,
                 level = logging.INFO,
                 ):
        self.commands = self.build_command()
        self.filename = self.build_filename()
        self.version = self.build_version()
        self.out_filename = self.set_out_filename(self.filename)
        self.logger = setup_logger(self.version, level=level)
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

    @staticmethod
    @abstractmethod
    def build_filename() -> str:
        pass

    @staticmethod
    @abstractmethod
    def build_version() -> str:
        pass

    @staticmethod
    def set_out_filename(filename: str) -> str:
        now_date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        return filename + "_" + now_date

    def write_log(self):
        """
        output command results
        :return:
        """
        if self.results is None:
            self.run()

        self.logger.info(f'--- write to {self.out_filename}')
        with open(self.out_filename, mode="w") as f:
            for text in self.results:
                text = str(text).lstrip("b'")
                text = str(text).lstrip("'")
                f.write(text + "\n")
                self.logger.debug(text)
        self.logger.info('--- end to write logs ---')

    def run(self) -> None:
        self.results = self.ssh_client.execute_command().split("\n")
        print(self.results)
        self.logger.info(self.results)


class FetchFileList(ExecutorInterface):
    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls -l",
            "df"
        ]

    @staticmethod
    def build_filename() -> str:
        return "filename"

    @staticmethod
    def build_version() -> str:
        return "FetchFileList"


def main():

    ip = "192.168.64.2"
    objects = FetchFileList(
        ip=ip, username=Config.USERNAME, password=Config.PASSWORD, port=Config.PORT, level=Config.LEVEL)
    print(
        objects.out_filename, objects.version)
    # objects.run()
    objects.write_log()


if __name__ == '__main__':
    main()

