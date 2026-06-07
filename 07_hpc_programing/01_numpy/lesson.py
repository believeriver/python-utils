import numpy as np

# Step1 基本的なsolve

A = np.array([[2.0, 1.0], [1.0, 3.0]])
b = np.array([5.0, 7.0])

# 内部でLU分解、早くて安定
x = np.linalg.solve(A, b)
print("解 x:", x)

# Step2 検証（残渣チェック）
residual = np.linalg.norm(A @ x - b)
print("残渣のノルム ||Ax - b||:", residual)

# Step3 逆行列との違い
print( np.linalg.inv(A) @ b ) # 逆行列を使うと数値的に不安定になる可能性がある
print( np.linalg.solve(A, b) ) # solveは安定している

# Step4 1D ポアソン方程式（CFDの圧力ソルバーの最小版）
# du^2/dx^2 = f(x) を離散化して Au = f の形にする(ディリクレ境界条件 u(0)=u(n+1)=0)
# 差分近似： -u[i-1] + 2u[i] - u[i+1] = h^2 f[i]
N = 10 # 内部格子の点数
h = 1.0 / (N + 1) # 格子間隔
f = np.ones(N) # 右辺のソース項（例: 一様なソース）

A_poisson = (2 * np.eye(N) - np.eye(N,k=1) - np.eye(N,k=-1)) / h**2

print("\nポアソン係数行列　A：")
print(np.round(A_poisson, 1))

# ソルバーで解く
u = np.linalg.solve(A_poisson, f)
print("\nポアソン方程式の解 u：")
print(np.round(u, 4))

# 厳密解との比較：u_exact = x(1-x)/2
x_grid = np.linspace(h, 1-h, N) # 内部格子点
u_exact = x_grid * (1 - x_grid) / 2
print("\n厳密解 u_exact：")
print(np.round(u_exact, 4))
print("\n数値解と厳密解の誤差：")
print(np.max(np.abs(u - u_exact)))
