import asyncio
import time

async def task(name: str, seconds: float) -> None:
    print(f"{name} 開始")
    await asyncio.sleep(seconds)
    print(f"{name} 終了")

async def main():
    # gatherに渡したコルーチンは「同時に」開始され、並行に進む
    await asyncio.gather(
        task("Task-A", 2),
        task("Task-B", 2),
    )

start = time.perf_counter()
asyncio.run(main())
elapsed = time.perf_counter() - start
print(f"\n実行時間: {elapsed:.2f}秒(gatherにより並行実行された)")
