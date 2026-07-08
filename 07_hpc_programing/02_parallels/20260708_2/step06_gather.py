"""
ステップ6: gather()はcreate_task + awaitをまとめた便利関数

前のステップで書いたこの2ステップを:
    task_a = asyncio.create_task(...)
    task_b = asyncio.create_task(...)
    await task_a
    await task_b

gatherは1行でまとめて書けるようにしたもの:
    await asyncio.gather(coro_a, coro_b)

Threadとの対比:
    Thread版: [t.join() for t in threads] で全Thread完了を待つ
    asyncio版: await gather(*tasks) で全タスク完了を待つ

さらにgatherの特徴:
    - 渡した順番で結果を返す(終わった順ではない)
    - return_exceptions=True で、失敗分を例外オブジェクトとして受け取れる
"""
import asyncio
import time

async def ssh_task(host: str, seconds: float) -> str:
    await asyncio.sleep(seconds)
    return f"{host}の結果"

async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 6)]

    print("=== gather: 複数タスクをまとめて並行実行 ===")
    start = time.perf_counter()
    results = await asyncio.gather(
        *(ssh_task(h, 1.0) for h in hosts)
    )
    elapsed = time.perf_counter() - start

    print(f"5台を並行処理: {elapsed:.2f}秒")
    print(f"結果(渡した順): {results}\n")

    print("=== create_task版(gatherと等価) ===")
    start = time.perf_counter()
    tasks = [asyncio.create_task(ssh_task(h, 1.0)) for h in hosts]
    results2 = [await t for t in tasks]
    elapsed = time.perf_counter() - start

    print(f"5台を並行処理: {elapsed:.2f}秒")
    print(f"結果: {results2}")

asyncio.run(main())
