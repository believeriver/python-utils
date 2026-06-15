import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rc('font', family='Hiragino Sans')

# ============================================================
# Step 1: 2Dポアソン行列の組み立て
# ∂²u/∂x² + ∂²u/∂y² = -f(x,y)
# クロネッカー積を使って1D行列から2D行列を構築
# ============================================================

N = 30
h = 1.0 /(N+1)

# 1D ポアソン行列（x方向 or y方向）
T1d = sp.diags(
    [2*np.ones(N), -np.ones(N-1), -np.ones(N-1)],
    [0, 1, -1], format='csr'
) / h**2

# print(T1d)

I_N = sp.eye(N, format='csr')

# 2D ポアソン行列:クロネッカー積で組み立て
# A2d = T1d @ I + I @ T1d
A2d = sp.kron(T1d, I_N) + sp.kron(I_N, T1d)

print(f"行列サイズ: {A2d.shape}")
print(f"非ゼロ要素数: {A2d.nnz}")
print(f"密度: {A2d.nnz / (N*N)**2 * 100:.4f}%")
print(f"疎行列メモリ: {A2d.nnz * 8 / 1e6:.2f} MB")
print(f"密行列なら:   {(N*N)**2 * 8 / 1e6:.1f} MB")

