from typing import List

from executor import ParamikoSSHClient, SSHClientSubprocess,ISSHExecutorInterface
from device_profiles import get_profile


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

    def build_command(self) -> List[str]:
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
# Switch Inventory Fetch Executor.


class FetchInventoryExecutor(ISSHExecutorInterface):
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    def build_command(self) -> List[str]:
        profile = get_profile(self.server_info.hardware_model)
        return profile.PRE_COMMANDS + profile.INVENTORY_CMDS

    @property
    def name(self) -> str:
        return "FetchInventoryExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        return self.result


class FetchCdpExecutor(ISSHExecutorInterface):
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    def build_command(self) -> List[str]:
        profile = get_profile(self.server_info.hardware_model)
        return profile.PRE_COMMANDS + [profile.CDP_CMD]

    @property
    def name(self) -> str:
        return "FetchCdpExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        return self.result


class FetchMacTableExecutor(ISSHExecutorInterface):
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    def build_command(self) -> List[str]:
        profile = get_profile(self.server_info.hardware_model)
        return profile.PRE_COMMANDS + [profile.MAC_TABLE_CMD]

    @property
    def name(self) -> str:
        return "FetchMacTableExecutor"

    def execute_command(self):
        self.execute()
        self.write_log()
        return self.result


class FetchArpExecutor(ISSHExecutorInterface):
    @staticmethod
    def build_ssh_client_cls():
        return ParamikoSSHClient

    def build_command(self) -> List[str]:
        profile = get_profile(self.server_info.hardware_model)
        if not profile.SUPPORTS_ARP:
            return []
        return profile.PRE_COMMANDS + [profile.ARP_CMD]

    @property
    def name(self) -> str:
        return "FetchArpExecutor"

    def execute_command(self):
        commands = self.build_command()
        if not commands:
            self.logger.info(
                f"{self.server_info.hostname}: hardware_model="
                f"{self.server_info.hardware_model} はARP非対応のためスキップ"
            )
            return []
        self.execute()
        self.write_log()
        return self.result