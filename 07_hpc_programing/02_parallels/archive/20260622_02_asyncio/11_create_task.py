import asyncio
import time

async def task(name: str, seconds: float) -> str:
    print(f"{name} 開始")
    await asyncio.sleep(seconds)
    print(f"{name} 終了")
    return f"{name}の結果"

async def main():
    # create_task() を呼んだ瞬間に、イベントループにスケジュールされ、
    # バックグラウンドで実行が始まる(gatherを使っていない)
    t1 = asyncio.create_task(task("Task-A", 2))
    t2 = asyncio.create_task(task("Task-B", 2))

    print("両方のタスクをスケジュールした直後(まだ完了を待っていない)")

    # 後で結果が必要になったタイミングでawaitする
    result_a = await t1
    result_b = await t2

    print(f"\n結果: {result_a}, {result_b}")

start = time.perf_counter()
asyncio.run(main())
elapsed = time.perf_counter() - start
print(f"実行時間: {elapsed:.2f}秒")
