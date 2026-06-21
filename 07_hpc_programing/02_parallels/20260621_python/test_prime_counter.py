"""
prime_counter.py のテスト。

ポイント: 並行処理(Thread/Process)のテストは難しいので、
まず「計算ロジックそのもの」を並行処理と無関係な形でテストする。
これが通っていれば、後で並行化しても計算結果は信用できる。
"""
from prime_counter import is_prime, count_primes_in_range


def test_is_prime_known_values():
    # 既知の素数・非素数で動作を確認
    assert is_prime(2) is True
    assert is_prime(17) is True
    assert is_prime(1) is False
    assert is_prime(0) is False
    assert is_prime(-5) is False
    assert is_prime(4) is False
    assert is_prime(97) is True


def test_count_primes_in_small_range():
    # [2, 20) の素数は 2,3,5,7,11,13,17,19 の8個
    assert count_primes_in_range(2, 20) == 8


def test_count_primes_in_range_is_consistent_with_is_prime():
    # count_primes_in_range が is_prime と矛盾しないことを確認
    start, end = 100, 200
    expected = sum(1 for n in range(start, end) if is_prime(n))
    assert count_primes_in_range(start, end) == expected


def test_count_primes_empty_range():
    assert count_primes_in_range(10, 10) == 0
