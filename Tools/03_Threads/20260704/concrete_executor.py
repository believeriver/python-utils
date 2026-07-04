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


class FetchInventoryExecutor(ISSHExecutorInterface):
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    @staticmethod
    def build_command() -> List[str]:
        return [
            "show version",
            "show inventory",
        ]

    @property
    def name(self) -> str:
        return "FetchInventoryExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        return self.result  # スライスせず全行返す
