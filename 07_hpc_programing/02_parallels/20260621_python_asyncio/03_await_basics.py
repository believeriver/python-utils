import asyncio
import time

async def task(name: str, seconds: float) -> None:
    print(f"{name} 開始")
    await asyncio.sleep(seconds)  # ここで「他の処理に制御を譲る」
    print(f"{name} 終了")

async def main():
    # これは「順番に」実行される(まだ並行ではない)
    await task("Task-A", 2)
    await task("Task-B", 2)

start = time.perf_counter()
asyncio.run(main())
elapsed = time.perf_counter() - start
print(f"\n実行時間: {elapsed:.2f}秒(awaitを順に呼んだだけなので、並行になっていない)")
