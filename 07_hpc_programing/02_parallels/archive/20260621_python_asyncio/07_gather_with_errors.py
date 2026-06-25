import asyncio

async def fetch_data(server_name: str, should_fail: bool) -> dict:
    await asyncio.sleep(0.2)
    if should_fail:
        raise ConnectionError(f"{server_name} への接続に失敗")
    return {"server": server_name, "status": "ok"}

async def main_default_behavior():
    """デフォルト: 1つでも例外が起きると、gather全体が例外を投げる"""
    print("--- デフォルト動作 ---")
    try:
        results = await asyncio.gather(
            fetch_data("switch-A", should_fail=False),
            fetch_data("switch-B", should_fail=True),   # これが失敗する
            fetch_data("switch-C", should_fail=False),
        )
        print(results)
    except ConnectionError as e:
        print(f"例外が発生: {e}")
        print("→ switch-A, switch-Cの結果も失われてしまった")

async def main_return_exceptions():
    """return_exceptions=True: 失敗した分は例外オブジェクトとして結果に含める"""
    print("\n--- return_exceptions=True ---")
    results = await asyncio.gather(
        fetch_data("switch-A", should_fail=False),
        fetch_data("switch-B", should_fail=True),
        fetch_data("switch-C", should_fail=False),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"  失敗: {r}")
        else:
            print(f"  成功: {r}")

asyncio.run(main_default_behavior())
asyncio.run(main_return_exceptions())
