"""
ステップ3: awaitが「何をしているか」

awaitは2つの意味を同時に持つ:
    (1) 「このコルーチンが完了するまで待つ」
    (2) 「待っている間、他のコルーチンに制御を譲る」

(1)だけ見ると「ブロッキングと同じじゃないか」と思えるが、
(2)があることで、複数のコルーチンが「待ち時間を共有」できる。

Threadとの対比:
    Thread版では time.sleep(1) はそのスレッドを1秒間占有する。
    他のスレッドはOSが判断して動かす。

    asyncio版では asyncio.sleep(1) は
    「1秒後にまたここに戻ってきてほしい」とイベントループに伝えて、
    その間、制御をイベントループに返す。
    → イベントループが「では他のコルーチンを動かそう」と判断できる。

重要: time.sleep() と asyncio.sleep() は全く別物
    time.sleep()    → そのスレッド全体を止める(ブロッキング)
    asyncio.sleep() → イベントループに制御を返す(非ブロッキング)
"""
import asyncio
import time

async def show_await_behavior():
    print("[1] awaitの前")
    await asyncio.sleep(1)   # ← ここで「1秒後に戻ってきて」とイベントループへ制御を返す
    print("[3] awaitの後(1秒後に戻ってきた)")

async def another_task():
    # もし他にタスクがあれば、上のawait中にここが動ける
    print("[2] (awaitの間に別タスクが動くポイント)")

async def main():
    print("--- awaitの動きを観察 ---")
    await show_await_behavior()

    print("\n--- time.sleep(NG) vs asyncio.sleep(OK) の違い ---")
    print("time.sleep()を使うと...")
    before = time.perf_counter()
    # これをasyncio環境内でやると、イベントループ全体を1秒止めてしまう
    time.sleep(0.5)  # ← 本来はasyncio内では使わない(後で実感する)
    after = time.perf_counter()
    print(f"  イベントループが {after - before:.2f}秒、完全に止まった")

asyncio.run(main())
