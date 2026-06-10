import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt


# 問題設定

N = 50         # 格子点数
alpha = 1.0    # 熱拡散率
L = 1.0        # 領域長さ
h = L / (N + 1) # 格子幅
x = np.linspace(h, L - h, N)

# 初期条件：山形（sin派）
u0 = np.sin(np.pi * x)

# 境界条件：両端 u=0（ディリクレ）

# ラプラス演算子の疎行列
diags = [2*np.ones(N), -np.ones(N-1), -np.ones(N-1)]
A_sparse = sp.diags(diags, [0,1,-1], format='csr') / h**2

# Step1: 陽解放（Explicit / Forward Euler)
# CFL条件を満たすために小さい時間ステップを選ぶ
dt_stable = 0.4 * h**2 / alpha # 安定境界の40%(余裕を持つ)
dt_unstable = 2.0 * h**2 / alpha # 安定境界の200%(不安定, 発散する)
t_end = 0.1

def explicit_euler(dt):
    u = u0.copy()
    t = 0.0
    history = [u.copy()]
    times = [0.0]
    while t < t_end:
        u -= dt * alpha * (A_sparse @ u)  # u^{n+1} = u^n - Δt·α·Au^n
        t += dt
        if len(history) == 6: # 最初の5ステップだけ保存
            history.append(u.copy())
            times.append(t)
    return u, history, times

u_stable, hist_stable, t_stable = explicit_euler(dt_stable)
u_unstable, hist_unstable, t_unstable = explicit_euler(dt_unstable)

print(f"安定なΔt={dt_stable:.6f}: 最大値={np.max(np.abs(u_stable)):.4f}")
print(f"不安定Δt={dt_unstable:.6f}: 最大値={np.max(np.abs(u_unstable)):.2e}  ← 発散")

