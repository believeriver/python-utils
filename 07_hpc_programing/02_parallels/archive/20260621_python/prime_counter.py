"""
素数カウントのコア処理。
CPUだけを使う処理であることが重要(I/O待ちがあるとGILの比較が崩れる)。
"""


def is_prime(n: int) -> bool:
    """nが素数かどうかを判定する。"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def count_primes_in_range(start: int, end: int) -> int:
    """[start, end) の範囲にある素数の個数を返す。"""
    return sum(1 for n in range(start, end) if is_prime(n))
