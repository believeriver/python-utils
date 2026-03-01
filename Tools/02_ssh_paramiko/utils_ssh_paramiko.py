from abc import ABC, abstractmethod
import paramiko
import subprocess
import datetime
import time
import os
import logging
import json
from typing import List, Type
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
        self.logger.debug(f"--- execute command: {self.commands} ---")
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
                 out_dir: str = None,
                 level = logging.INFO,
                 ):
        self.commands = self.build_command()
        self.filename = self.build_filename()
        self.version = self.build_version()
        self.out_filename = self.set_out_filename(self.filename, out_dir)
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
    def set_out_filename(filename: str, out_dir) -> str:
        now_date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        if out_dir is None:
            return filename + "_" + now_date
        else:
            return out_dir + "/" + filename + "_" + now_date

    def write_log(self):
        """
        output command results
        :return:
        """
        if self.results is None:
            self.run()

        self.logger.info(f'--- write to {self.out_filename} ---')
        with open(self.out_filename, mode="w") as f:
            for text in self.results:
                text = str(text).lstrip("b'")
                text = str(text).lstrip("'")
                f.write(text + "\n")
                self.logger.debug(text)
        self.logger.debug('--- end to write logs ---')

    def run(self) -> None:
        self.results = self.ssh_client.execute_command().split("\n")
        # for text in self.results:
        #     self.logger.info(text)


# Concrete Executor.
class FetchFileListExecutor(ExecutorInterface):
    @staticmethod
    def build_command() -> List[str]:
        return [
            "ls -l",
            "df"
        ]

    @staticmethod
    def build_filename() -> str:
        return "file_list"

    @staticmethod
    def build_version() -> str:
        return "fetch_file_list_executor"


#-----------------
# Utils
#-----------------
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
            items = f.readlines()

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


#-------------
# Orchestrator
#-------------
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
        self.logger = setup_logger('FetchLogFactory', level=self.level)
        self.config_file = None
        self.output_dir = None
        self.create_file_path()
        self.summary = []

    def create_file_path(self):
        cur_dir = os.getcwd()
        self.config_file = os.path.join(cur_dir, "settings", "config.ini")
        self. output_dir = os.path.join(cur_dir, "out")
        self.logger.debug(f"config file: {self.config_file}")
        self.logger.debug(f"output_dir: {self.output_dir}")

    def fetch_summary(self, hostname: str, ipaddr: str, command_result: List[str]):
        """

        :return:
        """
        result = dict()
        result['HOSTNAME'] = hostname
        result['IPADDR'] = ipaddr
        texts = []
        for text in command_result:
            text = str(text).lstrip("b'")
            text = str(text).lstrip("'")
            print(text)
            texts.append(text)
        result['COMMAND_RESULT'] = texts
        self.summary.append(result)

    def fetch_log_from_targets(self):
        dataset = self.dataset_cls(self.config_file)
        for cnt in range(len(dataset.ipaddr_list)):
            print(f' --- {cnt} ---')
            print(f'hostname : {dataset.hostname_list[cnt]}')
            print(f'ipaddr   : {dataset.ipaddr_list[cnt]}')
            executor_cls = self.executor_cls(
                ip=dataset.ipaddr_list[cnt],
                username=self.username, password=self.password,
                port=self.port, out_dir=self.output_dir, level=self.level)
            executor_cls.run()
            # executor_cls.write_log()
            self.fetch_summary(hostname=dataset.hostname_list[cnt],
                               ipaddr=dataset.ipaddr_list[cnt],
                               command_result=executor_cls.results)


def main(executor_cls: Type[ExecutorInterface]):

    cur_dir = os.getcwd()
    config_file = os.path.join(cur_dir, "settings", "config.ini")
    output_dir = os.path.join(cur_dir, "out")
    print({"[INFO] config.ini: ", config_file})
    dataset = SwitchListDataset(config_file)
    print(dataset)
    # ip = "192.168.64.2"
    executor = executor_cls(
        ip=dataset.ipaddr_list[0], username=Config.USERNAME, password=Config.PASSWORD,
        port=Config.PORT, out_dir=output_dir,level=Config.LEVEL)
    executor.write_log()


if __name__ == '__main__':
    ex = FetchFileListExecutor
    main(ex)

