# 表示グループの定義
# キー: エリア名(ダッシュボード上に縦に並べて全表示される)
# 値: そのエリアに属するCSVカラム名のリスト
AREA_GROUPS = {
    "ライセンス": ["NASTRAN", "Abaqus", "Fluent", "CFX"],
    "X流体機": ["X1_Haswell", "X1_Broadwell", "X1_Skylake"],
    "Y流体機": ["Y2_Broadwell", "Y2_Broadwell2", "Y2_Skylake"],
}

# 逼迫とみなす閾値(ランキング表示の色分けに使用)
WARNING_THRESHOLD = 90
CAUTION_THRESHOLD = 50
