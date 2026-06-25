import asyncio

async def slow_switch(host: str, response_time: float) -> str:
    """応答が遅い(または応答しない)スイッチを模擬。"""
    print(f"[{host}] 問い合わせ送信...")
    await asyncio.sleep(response_time)
    print(f"[{host}] 応答受信")
    return f"{host}からの応答"

async def main():
    # 応答時間5秒のスイッチに対して、3秒でタイムアウトさせる
    try:
        result = await asyncio.wait_for(
            slow_switch("switch-999", response_time=5.0),
            timeout=3.0,
        )
        print(f"結果: {result}")
    except asyncio.TimeoutError:
        print("→ タイムアウト発生(3秒経過しても応答なし)")

asyncio.run(main())
