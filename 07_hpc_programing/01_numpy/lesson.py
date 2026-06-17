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

# ============================================================
# Step 2: 右辺（ソース項）と境界条件
# f(x,y) = 2π² sin(πx)sin(πy)
# 厳密解: u(x,y) = sin(πx)sin(πy)
# ============================================================
x = np.linspace(h, 1-h, N)
y = np.linspace(h, 1-h, N)
X, Y = np.meshgrid(x, y)
# print(x, y, X)

f2d = 2 * np.pi**2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
b = f2d.ravel()  # 2D配列を1Dベクトルに変換

# ============================================================
# Step 3: 解く（直接法 vs CG+ILU）
# ============================================================
import time
# 直接法
t0 = time.time()
u_direct = spla.spsolve(A2d, b)
print(f"\n直接法の計算時間: {time.time() - t0:.3f} 秒")

# ILU前処理つきCG
ilu = spla.spilu(A2d.tocsc(), fill_factor=10)
M = spla.LinearOperator(A2d.shape, ilu.solve)

iters = [0]

def cb(xk): iters[0] += 1

t0 = time.time()
u_cg, info = spla.cg(A2d, b, M=M, rtol=1e-9, callback=cb)
print(f"CGの計算時間: {time.time() - t0:.3f} 秒, 反復回数: {iters[0]}")

# ============================================================
# Step 4: 厳密解との比較
# ============================================================
u_exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
u2d = u_direct.reshape(N, N)

print(f"\n最大誤差（直接法）: {np.max(np.abs(u2d - u_exact)):.2e}")

# ============================================================
# Step 5: 可視化
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 数値解
im0 = axes[0].contourf(X, Y, u2d, levels=20, cmap='hot')
axes[0].set_title('数値解 u(x, y)')
axes[0].set_xlabel('x'); axes[0].set_ylabel('y')
plt.colorbar(im0, ax=axes[0])

