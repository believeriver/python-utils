import asyncio

# 「今、同時に何台が処理中か」を数えるための共有変数
current_concurrent = 0
max_concurrent_seen = 0

async def query_switch(host: str):
    global current_concurrent, max_concurrent_seen
    current_concurrent += 1
    max_concurrent_seen = max(max_concurrent_seen, current_concurrent)

    await asyncio.sleep(0.3)  # 通信時間を模擬

    current_concurrent -= 1
    return {"host": host, "status": "ok"}

async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 101)]  # 100台

    await asyncio.gather(*(query_switch(h) for h in hosts))

    print(f"同時実行数の最大値: {max_concurrent_seen}台")
    print("→ 制限なしだと、100台すべてが同時に実行されてしまう")

asyncio.run(main())
