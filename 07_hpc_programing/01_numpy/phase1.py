import numpy as np


# Phase1
# 配列の基本

a = np.array([1.0, 2.0, 3.0])
A = np.array([[1, 2], [3, 4]], dtype=float)

print("shape of a:", A.shape)
print("dtype of a:", A.dtype)

# 配列の演算

B = np.array([[5, 6], [7, 8]], dtype=float)

print('加算　　　　：', A + B) # 要素ごとの加算
print('行列積　　　：', A @ B) # 行列積
print('Hadamard積：', A * B) # 要素ごとの乗算(Hadamard積)
print('除算　　　　：', A / B) # 要素ごとの除算
print('転置　　　　：', A.T) # 転置
print('逆行列　　　：', np.linalg.inv(A)) # 逆行列
print('行列式　　　：', np.linalg.det(A)) # 行列式
print('固有値と固有ベクトル：', np.linalg.eig(A)) # 固有値と固有ベクトル

# ブロードキャスト
v = np.array([50.0, 60.0])
print(A + v)

# スライスとビュー
C = np.zeros((4,4))
C[1:3, 1:3] = A
print(C)

# Phase2