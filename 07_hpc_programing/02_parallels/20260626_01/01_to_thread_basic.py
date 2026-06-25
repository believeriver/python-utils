"""
既存の「同期的な」ISSHExecutorInterface(paramiko/subprocessベース)を、
1行も変更せずに asyncio.to_thread() でラップする方法のデモ。

ポイント:
    - ISSHExecutorInterface, SSHClientSubprocess, ParamikoSSHClient は変更不要。
    - 呼び出し側だけが async def になり、
      executor.execute_command() を直接呼ぶ代わりに
      await asyncio.to_thread(executor.execute_command) を呼ぶ。
"""
import asyncio
import time


# ------------------------------------------------------------
# 既存コードの「模擬版」(実際は ISSHExecutorInterface のサブクラス)
# ここは元のコードと同じ「同期的な」インターフェースのまま、何も変えない。
# ------------------------------------------------------------
class SyncSSHExecutor:
    """既存のFetchLSDFExecutorなどに相当。同期的なexecute_command()を持つ。"""

    def __init__(self, hostname: str):
        self.hostname = hostname

    def execute_command(self) -> str:
        """
        本来はここで paramiko.SSHClient().connect(...) や
        subprocess.run(...) を呼ぶ(ブロッキング処理)。
        """
        time.sleep(0.3)  # ブロッキングI/Oを模擬(paramikoのconnect等に相当)
        return f"{self.hostname}: コマンド実行結果"


# ------------------------------------------------------------
# 呼び出し側(ここだけがasyncio対応になる)
# ------------------------------------------------------------
async def run_executor_async(executor: SyncSSHExecutor) -> str:
    """
    既存の同期メソッドを、別スレッドで実行してもらい、
    その完了をコルーチンとして待つ。

    asyncio.to_thread(関数, *args) という形で呼ぶ
    (関数そのものを渡す。呼び出し済みの結果ではなく、呼び出し可能なものを渡す点に注意)
    """
    result = await asyncio.to_thread(executor.execute_command)
    return result


async def main():
    hosts = [f"switch-{i:03d}" for i in range(1, 11)]
    executors = [SyncSSHExecutor(h) for h in hosts]

    start = time.perf_counter()
    # 既存の同期コードのままなのに、複数台へ並行アクセスできる
    results = await asyncio.gather(
        *(run_executor_async(ex) for ex in executors)
    )
    elapsed = time.perf_counter() - start

    print(f"実行時間: {elapsed:.2f}秒 (10台、各0.3秒のブロッキング処理)")
    print("→ 逐次なら3秒かかるはずが、to_threadにより並行化された")
    for r in results[:3]:
        print(f"  {r}")


if __name__ == "__main__":
    asyncio.run(main())