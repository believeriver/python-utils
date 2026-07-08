"""
ステップ1: 通常の関数とコルーチン関数の違い

Threadとの対比:
    Thread版では「関数」を Thread(target=func) に渡す。
    asyncio版では「コルーチン関数(async def)」を使う。
    どちらも「何をするか」を定義するだけで、
    呼んだだけでは実際には実行されない点がある。

    ただし違いがある:
    - 普通の関数: 呼んだ瞬間に実行が始まる
    - コルーチン関数: 呼んでも「コルーチンオブジェクト」が作られるだけ
"""

# 通常の関数
def greet_sync(name: str) -> str:
    print(f"Hello, {name}!")
    return f"{name}からの返答"

# コルーチン関数(async defをつけるだけ)
async def greet_async(name: str) -> str:
    print(f"Hello, {name}!")
    return f"{name}からの返答"


print("=== 通常の関数 ===")
result = greet_sync("Nobuyuki")     # 呼んだ瞬間に実行される
print(f"戻り値: {result}\n")

print("=== コルーチン関数 ===")
result = greet_async("Nobuyuki")    # 呼んでも実行されない
print(f"戻り値: {result}")          # コルーチンオブジェクトが返ってくる
print(f"型: {type(result)}")
result.close()  # 警告を出さないように閉じる
