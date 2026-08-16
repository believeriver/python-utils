from typing import List

from executor import ParamikoSSHClient, SSHClientSubprocess,ISSHExecutorInterface


"""
Date: 2026.08.16
Version: 1.0
Created by N.T
"""
# -----------------------------
# Concrete Executor.(Example)
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
        #
        #memo split
        # memo splitlines()は、改行コードを考慮して行ごとに分割する。改行コードは削除される。
        # self.result = self.result.split("\n")
        # text = self.result.splitlines()
        #
        self.execute()
        self.write_log()
        text = self.result
        text_lines = [ln for ln in text if ln.strip()]
        result = text_lines[1:2]
        return result


class FetchPWDExecutor(ISSHExecutorInterface):
    """
    2026.03.26
    pwd
    hostname
    2つ以上のコマンドを実行する例。
    ParamikoSSHClient()で実行することを想定（複数コマンドの実行はsubprocessだと少し面倒なので）。
    """
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    @staticmethod
    def build_command() -> List[str]:
        return [
            "pwd",
            "hostname"
        ]

    @property
    def name(self) -> str:
        return "FetchPWDExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        text = self.result
        text_lines = [ln for ln in text if ln.strip()]
        result = text_lines[1:2]
        return result


# -----------------------------
# Concrete Executor.
# command defined in cluster.ini
# -----------------------------
class ClusterCommandExecutor(ISSHExecutorInterface):
    """
    2026.08.14
    cluster.iniに定義されたコマンドを実行する例。
    ex)pacctデータを計算するPerlプログラムを実行する
    """
    # クラス変数としてデフォルトタイムアウトを持たせる
    DEFAULT_TIMEOUT = 3600  # pacct処理を考慮して長めに(要調整)

    @staticmethod
    def build_ssh_client_cls():
        return SSHClientSubprocess

    def build_command(self) -> List[str]:
        cluster_command = self.server_info.command
        print(f"[INFO] {self.server_info.hostname}:{cluster_command}")
        return [
            cluster_command,
        ]

    @property
    def name(self) -> str:
        return "ClusterCommandExecutor"

    def execute_command(self):
        self.execute()
        # self.write_log()
        return self.result
