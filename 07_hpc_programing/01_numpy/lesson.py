import numpy as np


# Step1 基本的な固有値分解

A = np.array([[3.0, 1.0], [1.0, 3.0]])
vals, vecs = np.linalg.eig(A)
print("固有値:", vals)
print("固有ベクトル:", vecs)

# 検証 A @ e = λ * e
for i in range(len(vals)):
    e = vecs[:, i]
    print(f"λ={vals[i]:.1f}: 残差 = {np.linalg.norm(A @ e - vals[i] * e):.2e}")


# step2 条件数 x(A) = λ_max / λ_min
N = 10
h = 1.0 / (N + 1)
A_p = (2*np.eye(N) - np.eye(N, k=1) - np.eye(N, k=-1))/ h**2
# A_p = (2*np.eye(N) - np.eye(N,k=1) - np.eye(N,k=-1)) / h**2

vals_p = np.linalg.eigvalsh(A_p) # 対称行列専用（高速・安定）
kappa = vals_p[-1] / vals_p[0]
print(f"\nN={N}: λ_max={vals_p[-1]:.1f}, λ_min={vals_p[0]:.1f}, κ={kappa:.1f}")

# Nを変えて条件数の変化を観察
for N in [5, 10, 20, 50]:
    h = 1.0 / (N + 1)
    A_p = (2*np.eye(N) - np.eye(N, k=1) - np.eye(N, k=-1)) / h**2
    # A_p = (2 * np.eye(N) - np.eye(N, k=1) - np.eye(N, k=-1)) / h ** 2
    v = np.linalg.eigvalsh(A_p)
    print(f"N={N}:  x = {v[-1]/v[0]:8.1f}")
