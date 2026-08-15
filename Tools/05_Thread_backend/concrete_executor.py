from typing import List

from executor import ParamikoSSHClient, SSHClientSubprocess,ISSHExecutorInterface


# -----------------------------
# Concrete Executor.
# -----------------------------

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


class PacctExecutor(ISSHExecutorInterface):
    """
    2026.08.14
    Pacctデータを計算するPerlプログラムを実行する
    """
    # クラス変数としてデフォルトタイムアウトを持たせる
    DEFAULT_TIMEOUT = 3600  # pacct処理を考慮して長めに(要調整)

    @staticmethod
    def build_ssh_client_cls():
        return SSHClientSubprocess

    def build_command(self) -> List[str]:
        cluster_command = self.server_info.command
        return [
            cluster_command,
        ]

    @property
    def name(self) -> str:
        return "PacctExecutor"

    def execute_command(self):
        self.execute()
        # self.write_log()
        return self.result
