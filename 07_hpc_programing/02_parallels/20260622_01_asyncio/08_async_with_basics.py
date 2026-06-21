import asyncio

class FakeSSHConnection:
    """
    SSH接続を模擬したクラス。
    async with で使うには、__aenter__ と __aexit__ という
    特殊メソッドを実装する(同期版の __enter__/__exit__ のasync版)。
    """

    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        # "async with X() as conn:" の "as conn" にあたる部分。
        # ここで実際の接続処理(時間がかかる想定)を行う。
        print(f"[{self.host}] 接続開始...")
        await asyncio.sleep(0.3)  # 接続確立にかかる時間を模擬
        print(f"[{self.host}] 接続完了")
        return self  # as の後の変数に渡されるオブジェクト

    async def __aexit__(self, exc_type, exc_value, traceback):
        # ブロックを抜けるとき、正常終了でも例外発生でも必ず呼ばれる。
        print(f"[{self.host}] 切断処理...")
        await asyncio.sleep(0.1)  # 切断にかかる時間を模擬
        print(f"[{self.host}] 切断完了")
        # Falseを返す(または何も返さない)と、例外はそのまま外に伝播する

    async def run_command(self, command: str) -> str:
        print(f"[{self.host}] コマンド実行: {command}")
        await asyncio.sleep(0.2)
        return f"{command}の実行結果(from {self.host})"


async def fetch_from_switch(host: str) -> str:
    async with FakeSSHConnection(host) as conn:
        result = await conn.run_command("show mac address-table")
        return result
    # ここを抜けた瞬間に __aexit__ が自動で呼ばれ、切断される


async def main():
    result = await fetch_from_switch("switch-001")
    print(f"\n最終結果: {result}")

asyncio.run(main())
