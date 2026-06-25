import asyncio
import random

async def query_switch(host: str) -> dict:
    """応答時間がランダムなスイッチへの問い合わせ。一部は極端に遅い(故障想定)。"""
    # 10%の確率で「応答しない」スイッチを混ぜる
    response_time = random.uniform(8.0, 10.0) if random.random() < 0.1 else random.uniform(0.1, 0.5)
    await asyncio.sleep(response_time)
    return {"host": host, "status": "ok"}


async def query_with_timeout(host: str, timeout: float = 2.0) -> dict:
    """個別にタイムアウトを設定し、タイムアウトも「結果の一種」として返す。"""
    try:
        return await asyncio.wait_for(query_switch(host), timeout=timeout)
    except asyncio.TimeoutError:
        return {"host": host, "status": "timeout"}


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 31)]  # 30台

    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(
        *(query_with_timeout(h, timeout=2.0) for h in hosts)
    )
    elapsed = asyncio.get_event_loop().time() - start

    ok_count = sum(1 for r in results if r["status"] == "ok")
    timeout_count = sum(1 for r in results if r["status"] == "timeout")

    print(f"実行時間: {elapsed:.2f}秒")
    print(f"正常応答: {ok_count}台, タイムアウト: {timeout_count}台")
    print("\nタイムアウトしたスイッチ:")
    for r in results:
        if r["status"] == "timeout":
            print(f"  {r['host']}")

asyncio.run(main())
