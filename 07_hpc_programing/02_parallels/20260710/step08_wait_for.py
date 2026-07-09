"""
ステップ8: asyncio.wait_for() によるタイムアウト

wait_for(コルーチン, timeout=秒数) で、指定時間内に終わらなければ
asyncio.TimeoutError を発生させてキャンセルする。

Threadとの対比:
    Thread版のParamikoSSHClientでは、timeout パラメータを
    paramiko の client.connect(timeout=...) に渡していた。
    これはparamiko側の機能なので「接続フェーズのタイムアウト」だけに効く。

    wait_for はコルーチン全体に対して外側から時間制限をかけられるので、
    「接続もコマンド実行もひっくるめて○秒まで」という制御が可能。

ポイント:
    タイムアウトを「エラー」ではなく「結果の一種」として扱うのが実務的な書き方。
    try/except で TimeoutError を受け取り、通常の結果と同じ形で返す。
"""
import asyncio
import random

async def connect_and_run(host: str) -> str:
    """応答時間がランダム。一部は極端に遅い(ハングしたスイッチを模擬)。"""
    # 10%の確率でハングを模擬
    delay = random.uniform(8.0, 10.0) if random.random() < 0.1 else random.uniform(0.1, 0.5)
    await asyncio.sleep(delay)
    return f"{host}: 応答あり"


async def fetch_with_timeout(host: str, timeout: float = 2.0) -> dict:
    """
    タイムアウトを「結果の一種」として返す設計。
    呼び出し側で TimeoutError を毎回 try/except しなくて済む。
    """
    try:
        result = await asyncio.wait_for(connect_and_run(host), timeout=timeout)
        return {"host": host, "status": "ok", "result": result}
    except asyncio.TimeoutError:
        return {"host": host, "status": "timeout", "result": None}


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 11)]

    results = await asyncio.gather(
        *(fetch_with_timeout(h, timeout=2.0) for h in hosts)
    )

    for r in results:
        status = "✓" if r["status"] == "ok" else "✗ TIMEOUT"
        print(f"  {r['host']}: {status}")

asyncio.run(main())
