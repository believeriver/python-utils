# test/test_executor.py
import logging
import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor import ServerInfo, SSHClientSubprocess, ISSHExecutorInterface


class DummyFileListExecutor(ISSHExecutorInterface):
    """テスト用の最小限Executor実装"""
    @staticmethod
    def build_ssh_client_cls():
        return SSHClientSubprocess

    def build_command(self):
        return ["ls -l /home"]

    @property
    def name(self):
        return "DummyFileListExecutor"

    def execute_command(self):
        self.execute()
        return self.result


def test_server_info_defaults():
    """ServerInfoが引数なしでデフォルト値を持つことを確認する単体テスト"""
    info = ServerInfo(ipaddr="192.168.64.2", hostname="rx8headnode")
    assert info.ipaddr == "192.168.64.2"
    assert info.hostname == "rx8headnode"


@pytest.mark.integration  # 実機依存のためマーカーで分離
def test_fetch_file_list_against_real_host(sample_one_target):
    """
    実際のSSH接続を伴う統合テスト。
    CI等では `pytest -m "not integration"` で除外する想定。
    """
    target = sample_one_target[0]
    server_info = ServerInfo(**target)
    executor = DummyFileListExecutor(server_info=server_info, level=logging.DEBUG)
    result = executor.execute_command()
    assert result is not None


# test$ pytest test_executor.py
