import asyncio

async def say_hello():
    print("こんにちは")

# asyncio.run() がイベントループを作り、コルーチンを実際に実行する
asyncio.run(say_hello())
