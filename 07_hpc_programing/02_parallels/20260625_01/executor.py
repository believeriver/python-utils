"""
asyncio版のSSH Executorインターフェース。

元のコード(ISSHExecutorInterface)との対応:
    - 同期版は __init__(server_info, timeout, level) を受け取り、
      execute_command() が同期的にSSHを実行する。
    - asyncio版では execute_command() を async def にし、
      内部で await asyncio.sleep(...) や await asyncio.to_thread(...) を使う。

ここではデモのため、実際のparamiko接続の代わりに、
ランダムな待ち時間と低確率の失敗を模擬する FakeAsyncSSHExecutor を使う。
"""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ServerInfo:
    """接続対象の情報。同期版のServerInfoに対応。"""

    hostname: str
    ipaddr: str
    username: str
    password: str


@dataclass(frozen=True)
class CommandResult:
    """1台に対する実行結果。成功/失敗を明示的に型で持たせる。"""

    hostname: str
    success: bool
    output: str | None = None
    error: str | None = None


class IAsyncSSHExecutorInterface(ABC):
    """同期版 ISSHExecutorInterface の asyncio版。"""

    def __init__(self, server_info: ServerInfo, timeout: float):
        self.server_info = server_info
        self.timeout = timeout

    @abstractmethod
    async def execute_command(self) -> CommandResult: ...


class FakeAsyncSSHExecutor(IAsyncSSHExecutorInterface):
    """
    デモ用の模擬Executor。
    実際の実装では、ここで paramiko を asyncio.to_thread() でラップするか、
    asyncssh など非同期対応ライブラリで接続する。
    """

    async def execute_command(self) -> CommandResult:
        host = self.server_info.hostname

        # 低確率で「応答しない」スイッチを模擬(timeoutで処理される想定)
        if random.random() < 0.05:
            await asyncio.sleep(self.timeout + 5)  # timeoutを超える長さ
        else:
            await asyncio.sleep(random.uniform(0.1, 0.4))

        # 低確率で「接続エラー」を模擬
        if random.random() < 0.05:
            return CommandResult(hostname=host, success=False, error="認証エラー")

        return CommandResult(
            hostname=host, success=True, output=f"{host}: show mac address-tableの結果"
        )
