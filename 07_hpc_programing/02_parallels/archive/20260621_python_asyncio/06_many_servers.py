import asyncio
import time
import random

async def fetch_data(server_name: str) -> dict:
    """サーバーへの問い合わせを模擬。応答時間はランダム(現実の揺らぎを表現)。"""
    delay = random.uniform(0.1, 0.5)
    await asyncio.sleep(delay)
    return {"server": server_name, "status": "ok", "delay": round(delay, 2)}

async def main():
    server_names = [f"switch-{i:03d}" for i in range(1, 101)]  # 100台分

    start = time.perf_counter()
    # リストをそのまま展開してgatherに渡す(* で展開)
    results = await asyncio.gather(
        *(fetch_data(name) for name in server_names)
    )
    elapsed = time.perf_counter() - start

    print(f"100台への問い合わせ完了: {elapsed:.2f}秒")
    print(f"取得件数: {len(results)}")
    print("先頭3件:")
    for r in results[:3]:
        print(f"  {r}")

asyncio.run(main())
