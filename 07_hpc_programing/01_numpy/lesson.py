import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import time

# Step1 蜜行列 vs 疎行列のメモリ比較

for N in [100, 1000, 5000]:
    dense_mb = N**2 * 8 /1e6

    # ポアソン行列の非ゼロ数：対角にN個、上下にN-1個ずつ
    nnz = N + 2*(N-1)
    sparse_mb = nnz * 8 / 1e6 # 値と列インデックスの両方を保存するために16バイト/
    print(f"N={N:5d} : Dense(密) {dense_mb:8.2f} MB, Sparse(疎) {sparse_mb:8.2f} MB")
    print(f"削減率={dense_mb/sparse_mb:6.1f}倍\n")


# Step2 : scipy.sparse　でポアソン行列を組立

N = 1000
h = 1.0 / (N + 1)

# diagsを使って対角行列を作成
diagonals = [2*np.ones(N), -1*np.ones(N-1), -1*np.ones(N-1)]
offsets = [0, 1, -1]
A_sparse = sp.diags(diagonals, offsets, format='csr') / h**2
b = np.ones(N)

print(f"\nAの形状：{A_sparse.shape}")
print(f"非ゼロ要素数：{A_sparse.nnz}")
print(f"密度：{A_sparse.nnz / (N**2) * 100:.4f}%")
print(f"メモリ使用量：{A_sparse.data.nbytes / 1e6:.2f} MB")
