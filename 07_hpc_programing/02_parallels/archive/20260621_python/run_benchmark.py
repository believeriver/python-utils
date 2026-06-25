"""
ベンチマークを実行して結果を表示するスクリプト。

このファイルの責務は「表示」だけ。計算ロジックも実行戦略の実装も持たない。
"""
import multiprocessing

from strategies import (
    SequentialStrategy,
    ThreadStrategy,
    ProcessStrategy,
    run_all_strategies,
    BenchmarkResult,
)


def print_results(results: list[BenchmarkResult]) -> None:
    for r in results:
        print(f"[{r.strategy_name:10s}] {r.elapsed_seconds:.3f}秒  "
              f"(素数の総数: {r.total_primes})")


if __name__ == "__main__":
    n_cores = multiprocessing.cpu_count()
    print(f"利用可能なCPUコア数: {n_cores}\n")

    N = 4
    chunk_size = 200_000
    ranges = [(i * chunk_size, (i + 1) * chunk_size) for i in range(N)]
    print(f"タスク数: {N}, 各タスクの範囲: {chunk_size}個の数を素数判定\n")

    strategies = [SequentialStrategy(), ThreadStrategy(), ProcessStrategy()]
    results = run_all_strategies(ranges, strategies)

    print_results(results)

    print("\n確認ポイント:")
    print("  thread が sequential とほぼ同じなら、GILの影響が確認できたことになる。")
    print("  process が明確に速くなっていれば、本当のCPU並列化ができている。")
