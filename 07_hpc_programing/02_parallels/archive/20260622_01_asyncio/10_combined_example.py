import asyncio
import random
import time

class FakeSSHConnection:
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        await asyncio.sleep(random.uniform(0.05, 0.2))
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await asyncio.sleep(0.02)  # 切断処理

    async def run_command(self, command: str) -> dict:
        await asyncio.sleep(random.uniform(0.05, 0.2))
        # 10%の確率で接続失敗を模擬
        if random.random() < 0.1:
            raise ConnectionError(f"{self.host}: タイムアウトまたは接続拒否")
        return {"host": self.host, "command": command, "status": "ok"}


async def fetch_one(host: str) -> dict:
    """1台のスイッチに対する処理。例外はここでは捕まえず、呼び出し元に委ねる。"""
    async with FakeSSHConnection(host) as conn:
        return await conn.run_command("show mac address-table")


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 51)]  # 50台

    start = time.perf_counter()
    results = await asyncio.gather(
        *(fetch_one(h) for h in hosts),
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - start

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [(h, r) for h, r in zip(hosts, results) if isinstance(r, Exception)]

    print(f"実行時間: {elapsed:.2f}秒")
    print(f"成功: {len(successes)}台, 失敗: {len(failures)}台")
    if failures:
        print("\n失敗したスイッチ:")
        for host, err in failures:
            print(f"  {host}: {err}")

asyncio.run(main())
