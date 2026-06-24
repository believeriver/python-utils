"""
ThreadWorkers(Thread + Queue + Lock)に対応する、asyncio版のワーカー。

設計のポイント:
    - Queueの代わりに、対象ホストのリストをそのままgatherに渡す。
    - Lockの代わりに、gatherが結果の集約を担う。
    - workers(Thread数)の代わりに、Semaphoreで同時実行数を制限する。
    - タイムアウトは個別にwait_forで設定し、結果の一種として扱う。
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Type

from executor import IAsyncSSHExecutorInterface, ServerInfo, CommandResult


@dataclass(frozen=True)
class AsyncSSHWorkerConfig:
    """ワーカーの設定値。Threadコードの引数群(workers, timeout, level)をまとめたもの。"""

    max_concurrent: int = 10  # 同時実行数(Threadコードのworkersに相当)
    timeout: float = 5.0
    log_level: int = logging.INFO


class AsyncSSHWorkers:
    """
    同期版 ThreadWorkers の asyncio版。

    使い方:
        worker = AsyncSSHWorkers(
            executor_cls=FakeAsyncSSHExecutor,
            targets=[server_info_1, server_info_2, ...],
            config=AsyncSSHWorkerConfig(max_concurrent=10, timeout=5.0),
        )
        results = await worker.run()
    """

    def __init__(
        self,
        executor_cls: Type[IAsyncSSHExecutorInterface],
        targets: list[ServerInfo],
        config: AsyncSSHWorkerConfig | None = None,
    ):
        self.executor_cls = executor_cls
        self.targets = targets
        self.config = config or AsyncSSHWorkerConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self.config.log_level)

        # Threadコードのself.result_lockに相当する保護は不要。
        # 代わりにSemaphoreで「同時に何台処理するか」を制御する。
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)

    async def _run_one(self, server_info: ServerInfo) -> CommandResult:
        """1台に対する処理。Semaphoreで同時実行数を絞り、wait_forでタイムアウトを設定する。"""
        async with self._semaphore:
            self.logger.debug(f"開始: {server_info.hostname}")
            executor = self.executor_cls(server_info=server_info, timeout=self.config.timeout)
            try:
                result = await asyncio.wait_for(
                    executor.execute_command(), timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                result = CommandResult(
                    hostname=server_info.hostname, success=False, error="タイムアウト"
                )
            self.logger.info(f"完了: {server_info.hostname} (success={result.success})")
            return result

    async def run(self) -> list[CommandResult]:
        """
        全対象への問い合わせを実行し、結果をまとめて返す。

        Threadコードのrun()との違い:
            - 戻り値が明示的にある(Threadコードはself.resultsに後で読み出す)
            - Sentinel値(None)による終了通知が不要
        """
        self.logger.debug(f"{len(self.targets)}台に対する処理を開始")
        results = await asyncio.gather(
            *(self._run_one(target) for target in self.targets)
        )
        self.logger.debug("全対象の処理が完了")
        return list(results)
