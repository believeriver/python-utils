import asyncio

current_concurrent = 0
max_concurrent_seen = 0

async def query_switch(host: str, semaphore: asyncio.Semaphore):
    global current_concurrent, max_concurrent_seen

    # semaphoreが許可した数だけ、ここを同時に通過できる
    async with semaphore:
        current_concurrent += 1
        max_concurrent_seen = max(max_concurrent_seen, current_concurrent)

        await asyncio.sleep(0.3)  # 通信時間を模擬

        current_concurrent -= 1

    return {"host": host, "status": "ok"}

async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 101)]  # 100台

    # 同時に10個までしか通過させない、という制限
    semaphore = asyncio.Semaphore(10)

    results = await asyncio.gather(
        *(query_switch(h, semaphore) for h in hosts)
    )

    print(f"同時実行数の最大値: {max_concurrent_seen}台")
    print(f"処理件数: {len(results)}台")
    print("→ Semaphore(10) により、常に最大10台までに制限された")

asyncio.run(main())
