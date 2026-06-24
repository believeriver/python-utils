"""
ThreadコードのmainTreads()/main()に対応する、asyncio版の実行スクリプト。
"""
import asyncio
import logging
import time

from executor import FakeAsyncSSHExecutor, ServerInfo
from async_workers import AsyncSSHWorkers, AsyncSSHWorkerConfig


def build_targets(n: int) -> list[ServerInfo]:
    """デモ用にN台分のServerInfoを作成。実際はConfig/SwitchListDatasetから読み込む部分に対応。"""
    return [
        ServerInfo(
            hostname=f"switch-{i:03d}",
            ipaddr=f"192.168.1.{i % 254 + 1}",
            username="admin",
            password="dummy",
        )
        for i in range(1, n + 1)
    ]


def print_summary(results: list) -> None:
    """同期版のReporterSample.print_results()に対応する表示処理。"""
    success = [r for r in results if r.success]
    failure = [r for r in results if not r.success]
    print(f"\n成功: {len(success)}台 / 失敗: {len(failure)}台")
    if failure:
        print("失敗した対象:")
        for r in failure:
            print(f"  {r.hostname}: {r.error}")


async def main():
    logging.basicConfig(level=logging.WARNING)  # ワーカー内ログはWARNING以上のみ表示

    targets = build_targets(n=100)
    config = AsyncSSHWorkerConfig(max_concurrent=15, timeout=3.0, log_level=logging.INFO)

    worker = AsyncSSHWorkers(
        executor_cls=FakeAsyncSSHExecutor,
        targets=targets,
        config=config,
    )

    start = time.perf_counter()
    results = await worker.run()
    elapsed = time.perf_counter() - start

    print(f"実行時間: {elapsed:.2f}秒 (対象: {len(targets)}台, 同時実行数: {config.max_concurrent})")
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
