import asyncio
import time

async def query_switch(host: str, semaphore: asyncio.Semaphore, response_time: float = 0.3):
    async with semaphore:
        await asyncio.sleep(response_time)
    return {"host": host, "status": "ok"}

async def run_with_limit(hosts: list[str], limit: int) -> float:
    semaphore = asyncio.Semaphore(limit)
    start = time.perf_counter()
    await asyncio.gather(*(query_switch(h, semaphore) for h in hosts))
    return time.perf_counter() - start

async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 201)]  # 200台

    for limit in [5, 20, 50, 200]:
        elapsed = await run_with_limit(hosts, limit)
        print(f"同時実行数={limit:3d}: {elapsed:.2f}秒")

asyncio.run(main())
