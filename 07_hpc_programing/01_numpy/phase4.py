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


# Step3 : ソルバー比較（前処理なし　vs ILU前処理）

# 収束履歴を記録するコールバック
residuals_cg = []
residuals__pcg = []

def cb_cg(xk):
    r = A_sparse @ xk - b
    residuals_cg.append(np.linalg.norm(r))

def cb_pcg(xk):
    r = A_sparse @ xk - b
    residuals__pcg.append(np.linalg.norm(r))

# 前処理なしのCG
t0 = time.time()
x_cg, info_cg = spla.cg(A_sparse, b, callback=cb_cg, rtol=1e-9)
t_cg = time.time() - t0

# ILU前処理を生成
ilu = spla.spilu(A_sparse.tocsc(), fill_factor=10)
M = spla.LinearOperator(A_sparse.shape, ilu.solve)

# CG with ILU前処理
t0 = time.time()
x_pcg, info_pcg = spla.cg(A_sparse, b, M=M, callback=cb_pcg, rtol=1e-9)
t_pcg = time.time() - t0

diff = A_sparse - A_sparse.T
print("対称性チェック:", diff.nnz)

# 最小固有値確認（正定値 = 全固有値 > 0）
vals = spla.eigsh(A_sparse, k=1, which='SM', return_eigenvectors=False)
print("最小固有値:", vals[0])  # 正の値なら OK

print(f"\nCG（前処理なし）：{len(residuals_cg):4d} 反復, 時間 {t_cg:.2f} 秒, info={info_cg}")
print(f"CG（ILU前処理）：{len(residuals__pcg):4d} 反復, 時間 {t_pcg:.2f} 秒, info={info_pcg}")
print(f"解の最大差：{np.max(np.abs(x_cg - x_pcg)):.2e}")


# Step4 : 直接法（spsolve）との比較

t0 = time.time()
x_direct = spla.spsolve(A_sparse, b)
t_direct = time.time() - t0
print(f"\n直接法（spsolve）：時間 {t_direct:.2f} 秒")
print(f"CG（前処理なし）と直接法の最大差：{np.max(np.abs(x_cg - x_direct)):.2e}")
print(f"CG（ILU前処理）と直接法の最大差：{np.max(np.abs(x_pcg - x_direct)):.2e}")