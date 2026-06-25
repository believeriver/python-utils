import asyncio

class FakeSSHConnection:
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        print(f"[{self.host}] 接続開始...")
        await asyncio.sleep(0.1)
        print(f"[{self.host}] 接続完了")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        print(f"[{self.host}] 切断処理...")
        await asyncio.sleep(0.1)
        if exc_type is not None:
            print(f"[{self.host}] 切断完了(例外 {exc_type.__name__} が発生していたが、それでも切断した)")
        else:
            print(f"[{self.host}] 切断完了(正常終了)")
        # False相当(何も返さない)なので、例外はこの後も外側に伝播する

    async def run_command(self, command: str) -> str:
        print(f"[{self.host}] コマンド実行: {command}")
        if command == "bad-command":
            raise RuntimeError(f"{self.host}でコマンドエラーが発生")
        await asyncio.sleep(0.1)
        return "ok"


async def fetch_from_switch(host: str) -> str:
    async with FakeSSHConnection(host) as conn:
        result = await conn.run_command("bad-command")  # ここで例外が起きる
        return result


async def main():
    try:
        await fetch_from_switch("switch-002")
    except RuntimeError as e:
        print(f"\nmain側で例外を受け取った: {e}")

asyncio.run(main())
