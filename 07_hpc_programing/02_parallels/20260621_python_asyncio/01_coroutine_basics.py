import asyncio

async def say_hello():
    print("こんにちは")

# 呼んでみる
result = say_hello()
print(f"呼んだ結果: {result}")
print(f"型: {type(result)}")
