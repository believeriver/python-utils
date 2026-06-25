import asyncio

async def background_logger():
    """終了を待つ必要のない、バックグラウンドで動き続ける処理の例。"""
    count = 0
    while True:
        await asyncio.sleep(1)
        count += 1
        print(f"  [バックグラウンド] {count}秒経過...")

async def fetch_data(name: str, seconds: float) -> str:
    await asyncio.sleep(seconds)
    return f"{name}のデータ"

async def main():
    # ログ出力のような「動かしっぱなしでいい」処理はcreate_taskで起動するだけ
    logger_task = asyncio.create_task(background_logger())

    # 本来の処理を進める
    result = await fetch_data("Server-X", 3.5)
    print(f"\nメイン処理結果: {result}")

    # background_loggerは無限ループなので、最後に明示的にキャンセルする
    logger_task.cancel()

asyncio.run(main())
