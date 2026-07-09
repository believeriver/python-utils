"""
ステップ9: asyncio.Semaphore による同時実行数の制限

Threadとの対比:
    Thread版では workers=5 のように「起動するThread数を固定」していた。
    つまりThread数 = 同時実行数。

    asyncio版では gather に全台分のタスクを一度に渡せるが、
    Semaphore を使わないと全台同時接続になってしまう。
    Semaphore(N) で「同時にNつまでしか中に入れない」という制限を設ける。

仕組み:
    async with semaphore: の中に入れるコルーチンはN個まで。
    N+1個目は「誰かが抜けるまで」自動的に待機する。
    → Thread版の Queue.get() で「空きが出るまで待つ」のと同じ効果。

使い方: Semaphore は1つ作って全タスクで共有する。
"""
import asyncio
import time

current_active = 0
max_active_seen = 0

async def fetch_one(host: str, semaphore: asyncio.Semaphore) -> dict:
    global current_active, max_active_seen

    async with semaphore:   # ← ここを通れるのは同時にN個まで
        current_active += 1
        max_active_seen = max(max_active_seen, current_active)

        await asyncio.sleep(0.3)  # SSH接続+コマンド実行を模擬

        current_active -= 1

    return {"host": host, "status": "ok"}


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 21)]  # 20台

    print("=== Semaphoreなし(全台同時) ===")
    global current_active, max_active_seen
    current_active = 0; max_active_seen = 0

    sem_unlimited = asyncio.Semaphore(99999)  # 実質制限なし
    start = time.perf_counter()
    await asyncio.gather(*(fetch_one(h, sem_unlimited) for h in hosts))
    elapsed = time.perf_counter() - start
    print(f"  実行時間: {elapsed:.2f}秒, 同時実行数の最大: {max_active_seen}台\n")

    print("=== Semaphore(5) ===")
    current_active = 0; max_active_seen = 0

    sem5 = asyncio.Semaphore(5)
    start = time.perf_counter()
    await asyncio.gather(*(fetch_one(h, sem5) for h in hosts))
    elapsed = time.perf_counter() - start
    print(f"  実行時間: {elapsed:.2f}秒, 同時実行数の最大: {max_active_seen}台\n")

    print("=== Semaphore(10) ===")
    current_active = 0; max_active_seen = 0

    sem10 = asyncio.Semaphore(10)
    start = time.perf_counter()
    await asyncio.gather(*(fetch_one(h, sem10) for h in hosts))
    elapsed = time.perf_counter() - start
    print(f"  実行時間: {elapsed:.2f}秒, 同時実行数の最大: {max_active_seen}台")

asyncio.run(main())
