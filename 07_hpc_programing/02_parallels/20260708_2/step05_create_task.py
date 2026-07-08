"""
ステップ5: create_task() で「並行に走らせる」

create_task()こそが「並行実行の開始」を意味する。
awaitは「完了を待つ」だけ。

Threadとの対比:
    Thread版:
        t1 = Thread(target=task, args=("A",)); t1.start()  # 並行開始
        t2 = Thread(target=task, args=("B",)); t2.start()  # 並行開始
        t1.join()  # 完了を待つ
        t2.join()  # 完了を待つ

    asyncio版:
        t1 = asyncio.create_task(task("A"))  # 並行開始 ← Thread.start()に相当
        t2 = asyncio.create_task(task("B"))  # 並行開始
        await t1  # 完了を待つ ← Thread.join()に相当
        await t2  # 完了を待つ
"""
import asyncio
import time

async def ssh_task(host: str, seconds: float) -> str:
    print(f"  {host}: 開始")
    await asyncio.sleep(seconds)
    print(f"  {host}: 完了")
    return f"{host}の結果"

async def main():
    print("=== OK: create_task()で並行実行 ===")
    start = time.perf_counter()

    # create_task() を呼んだ瞬間に、バックグラウンドで実行が始まる
    task_a = asyncio.create_task(ssh_task("switch-A", 1.0))
    task_b = asyncio.create_task(ssh_task("switch-B", 1.0))

    # この時点で両方のタスクはすでに動いている
    # await は「完了するまで待つ」だけ
    result_a = await task_a
    result_b = await task_b

    elapsed = time.perf_counter() - start
    print(f"  → 合計: {elapsed:.2f}秒 (2台×1秒 → 並行で約1秒)\n")
    print(f"  結果: {result_a}, {result_b}")

asyncio.run(main())
