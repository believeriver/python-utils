"""
3つの実行戦略(逐次 / Thread / Process)を共通インターフェースで揃える。

設計のポイント:
    - 「どう並列化するか」の違いだけを切り出し、
      計算ロジック(prime_counter.py)には一切手を加えない。
    - 結果は BenchmarkResult という dataclass で統一する。
      print に直接頼らず、戻り値としてテスト可能にする。
"""
from __future__ import annotations

import threading
import time
import multiprocessing
from dataclasses import dataclass
from typing import Protocol

from prime_counter import count_primes_in_range

Range = tuple[int, int]


@dataclass(frozen=True)
class BenchmarkResult:
    """1回のベンチマーク実行結果。"""

    strategy_name: str
    elapsed_seconds: float
    total_primes: int


class ExecutionStrategy(Protocol):
    """
    実行戦略の共通インターフェース。
    Protocolを使うことで、継承関係を作らずに「この形を持つクラスならOK」
    という制約だけを表現できる(ダックタイピングを型で保証する)。
    """

    name: str

    def run(self, ranges: list[Range]) -> BenchmarkResult: ...


class SequentialStrategy:
    """パターン1: シングルスレッドで逐次実行。"""

    name = "sequential"

    def run(self, ranges: list[Range]) -> BenchmarkResult:
        start_time = time.perf_counter()
        results = [count_primes_in_range(s, e) for s, e in ranges]
        elapsed = time.perf_counter() - start_time
        return BenchmarkResult(self.name, elapsed, sum(results))


class ThreadStrategy:
    """パターン2: threadingで並列実行のつもり(GILの影響を受ける)。"""

    name = "thread"

    def run(self, ranges: list[Range]) -> BenchmarkResult:
        results: list[int | None] = [None] * len(ranges)

        def worker(idx: int, start: int, end: int) -> None:
            results[idx] = count_primes_in_range(start, end)

        start_time = time.perf_counter()
        threads = [
            threading.Thread(target=worker, args=(idx, s, e))
            for idx, (s, e) in enumerate(ranges)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start_time
        return BenchmarkResult(self.name, elapsed, sum(results))  # type: ignore[arg-type]


class ProcessStrategy:
    """パターン3: multiprocessingで本当の並列実行。"""

    name = "process"

    def run(self, ranges: list[Range]) -> BenchmarkResult:
        start_time = time.perf_counter()
        with multiprocessing.Pool(processes=len(ranges)) as pool:
            results = pool.starmap(count_primes_in_range, ranges)
        elapsed = time.perf_counter() - start_time
        return BenchmarkResult(self.name, elapsed, sum(results))


def run_all_strategies(
    ranges: list[Range], strategies: list[ExecutionStrategy]
) -> list[BenchmarkResult]:
    """渡された戦略すべてを実行し、結果のリストを返す。"""
    return [strategy.run(ranges) for strategy in strategies]
