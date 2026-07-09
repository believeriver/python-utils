"""
ステップ10: async with + wait_for + Semaphore の統合

これがNobuyukiさんの「数百台のスイッチ管理」に使える
asyncioの実用的な基本パターン。

Threadコードとの対応:
    ThreadWorkers.worker()    → fetch_one()
    Queue + workers数のThread → gather + Semaphore
    threading.Lock            → 不要(gatherが集約)
    Config.TIMEOUT            → wait_for(timeout=...)
    paramiko finally close    → async with の __aexit__
"""
import asyncio
import random
import time


class SSHConnection:
    """SSH接続のリソース管理(async with用)。"""
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        await asyncio.sleep(0.05)  # 接続確立
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.01)  # 切断

    async def run_command(self, command: str) -> str:
        delay = random.uniform(0.1, 0.4)
        await asyncio.sleep(delay)
        return f"{self.host}: {command} 完了"


async def fetch_one(
    host: str,
    semaphore: asyncio.Semaphore,
    timeout: float,
) -> dict:
    """
    1台への問い合わせ。
    Semaphore で同時実行数を制限し、
    async with で接続を確実に閉じ、
    wait_for でタイムアウトを保証する。
    """
    async with semaphore:   # 同時実行数の制限
        try:
            async with SSHConnection(host) as conn:   # 接続の開始・終了保証
                result = await asyncio.wait_for(      # タイムアウト
                    conn.run_command("show mac address-table"),
                    timeout=timeout,
                )
            return {"host": host, "status": "ok", "result": result}

        except asyncio.TimeoutError:
            return {"host": host, "status": "timeout", "result": None}
        except Exception as e:
            return {"host": host, "status": "error", "result": str(e)}


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 51)]  # 50台

    semaphore = asyncio.Semaphore(10)   # 同時10台まで
    timeout = 1.0                        # 1秒でタイムアウト

    start = time.perf_counter()
    results = await asyncio.gather(
        *(fetch_one(h, semaphore, timeout) for h in hosts)
    )
    elapsed = time.perf_counter() - start

    ok      = [r for r in results if r["status"] == "ok"]
    timeout_ = [r for r in results if r["status"] == "timeout"]
    error   = [r for r in results if r["status"] == "error"]

    print(f"実行時間: {elapsed:.2f}秒 (50台, 同時10台, タイムアウト{timeout}秒)")
    print(f"成功: {len(ok)}台 / タイムアウト: {len(timeout_)}台 / エラー: {len(error)}台")

asyncio.run(main())
