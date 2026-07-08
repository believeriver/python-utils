"""
ステップ4: awaitを順番に呼ぶだけでは「並行にならない」

これがasyncioを学ぶ人が最も混乱するポイント。

Threadとの対比:
    Thread版では t.start() を呼んだ瞬間に並行実行が始まる。
        t1 = Thread(target=task); t1.start()  # ← ここで並行スタート
        t2 = Thread(target=task); t2.start()  # ← ここで並行スタート

    asyncio版では await task() を並べても「順次実行」になる。
        await task("A")  # ← Aが完全に終わるまでここで待つ
        await task("B")  # ← Bはその後

「awaitを呼ぶ = 完了まで待つ」という意味であって、
「並行に走らせる」という意味ではない。
"""
import asyncio
import time

async def ssh_task(host: str, seconds: float) -> str:
    print(f"  {host}: 開始")
    await asyncio.sleep(seconds)  # SSH接続の待ち時間を模擬
    print(f"  {host}: 完了")
    return f"{host}の結果"

async def main():
    print("=== NG: awaitを順番に呼ぶだけ(逐次実行になってしまう) ===")
    start = time.perf_counter()
    result_a = await ssh_task("switch-A", 1.0)  # 1秒待つ
    result_b = await ssh_task("switch-B", 1.0)  # さらに1秒待つ
    elapsed = time.perf_counter() - start
    print(f"  → 合計: {elapsed:.2f}秒 (2台×1秒 = 2秒、並行になっていない)\n")

asyncio.run(main())
