"""
ステップ2: asyncio.run() でコルーチンを実際に実行する

Threadとの対比:
    Thread版: t = Thread(target=func); t.start(); t.join()
              → start() で実行開始、join() で完了を待つ

    asyncio版: asyncio.run(coro())
              → イベントループを作り、コルーチンを実行して完了まで待つ
              → これが「プログラム全体の入り口」として1回だけ使う

イベントループとは:
    コルーチンを実際に動かす「司令塔」。
    「次はどのコルーチンを動かすか」を管理する仕組み。
    asyncio.run()が自動で作って、終わったら自動で閉じてくれる。
"""
import asyncio

async def greet(name: str) -> str:
    print(f"Hello, {name}!")
    return f"{name}からの返答"

# asyncio.run() に「コルーチンオブジェクト」を渡すことで実行される
result = asyncio.run(greet("Nobuyuki"))
print(f"戻り値: {result}")
