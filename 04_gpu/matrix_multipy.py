import time
import statistics
import torch


def sync_if_needed(device: torch.device):
    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize()


def bench_matmul(
        n=4096, repeats=20, warmup=5, dtype=torch.float32, device_str="cpu"):
    device = torch.device(device_str)

    # 入力生成
    a = torch.randn(n, n, device=device, dtype=dtype)
    b = torch.randn(n, n, device=device, dtype=dtype)

    # ウォームアップ
    for _ in range(warmup):
        c = a @ b
        sync_if_needed(device)

    # 計測
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        c = a @ b
        sync_if_needed(device)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    median = statistics.median(times)
    return median, times

def main():
    print("PyTorch:", torch.__version__)
    print("MPS available:", torch.backends.mps.is_available())

    # CPUスレッド固定（比較のブレを減らす）
    torch.set_num_threads(1)

    n = 4096  # まずは大きめでGPU有利になりやすい条件
    cpu_median, _ = bench_matmul(n=n, device_str="cpu")
    print(f"CPU median: {cpu_median:.4f} s (n={n})")

    if torch.backends.mps.is_available():
        mps_median, _ = bench_matmul(n=n, device_str="mps")
        print(f"MPS median: {mps_median:.4f} s (n={n})")
        print(f"Speedup (CPU/MPS): {cpu_median / mps_median:.2f}x")
    else:
        print("MPSが利用できません（macOS/torchの状況を確認してください）。")

if __name__ == "__main__":
    main()
