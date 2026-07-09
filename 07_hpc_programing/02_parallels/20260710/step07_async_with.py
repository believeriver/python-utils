"""
ステップ7: async with によるリソース管理

Threadとの対比:
    Thread版のParamikoSSHClientでは、finally: client.close() で
    「例外が起きても必ず接続を閉じる」を保証していた。

    asyncio版では async with が同じ役割を担う。
    ブロックを抜けたとき(正常終了でも例外でも)に必ず後処理が走る。

仕組み:
    async with X() as conn: というコードは
        1. X().__aenter__() を await して conn を得る  ← 接続開始
        2. ブロック内の処理を実行
        3. ブロックを抜けると X().__aexit__() を await  ← 接続終了(例外でも必ず)
"""
import asyncio

class SSHConnection:
    """SSH接続を模擬したクラス。"""
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        print(f"  [{self.host}] 接続開始")
        await asyncio.sleep(0.1)  # connect()の待ち時間を模擬
        print(f"  [{self.host}] 接続完了")
        return self  # as conn の conn になる部分

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"  [{self.host}] 切断処理(例外={exc_type})")
        await asyncio.sleep(0.05)
        print(f"  [{self.host}] 切断完了")
        # Noneを返す = 例外はそのまま外に伝播させる

    async def run_command(self, command: str) -> str:
        print(f"  [{self.host}] コマンド実行: {command}")
        await asyncio.sleep(0.1)
        return f"{self.host}: {command} の結果"


async def fetch_switch_data(host: str) -> str:
    async with SSHConnection(host) as conn:
        result = await conn.run_command("show mac address-table")
        return result
    # ここを抜けた瞬間に __aexit__ が呼ばれ、切断される


async def main():
    print("=== 正常終了の場合 ===")
    result = await fetch_switch_data("switch-001")
    print(f"  取得結果: {result}\n")

    print("=== 例外が起きても切断される ===")
    try:
        async with SSHConnection("switch-002") as conn:
            await conn.run_command("show version")
            raise ConnectionError("コマンド実行中にエラー発生")  # 意図的に例外
    except ConnectionError as e:
        print(f"  例外を受け取った: {e}")
    print("  ↑ 例外が起きても切断処理は必ず実行されている\n")

asyncio.run(main())
