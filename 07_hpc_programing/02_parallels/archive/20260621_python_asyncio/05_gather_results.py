import asyncio
import time

async def fetch_data(name: str, seconds: float) -> dict:
    """サーバーからデータを取得する処理を模擬。戻り値があることに注目。"""
    print(f"{name} 開始")
    await asyncio.sleep(seconds)
    print(f"{name} 終了")
    return {"name": name, "data": f"{name}から取得したデータ"}

async def main():
    # gatherは「渡した順番」で結果のリストを返す(終わった順ではない)
    results = await asyncio.gather(
        fetch_data("Server-A", 2.0),
        fetch_data("Server-B", 0.5),
        fetch_data("Server-C", 1.0),
    )
    return results

start = time.perf_counter()
results = asyncio.run(main())
elapsed = time.perf_counter() - start

print(f"\n実行時間: {elapsed:.2f}秒")
print("結果一覧(渡した順序で返ってくる):")
for r in results:
    print(f"  {r}")
