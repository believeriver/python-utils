# 表示グループの定義(3階層: エリア → サブグループ → 項目)
#
# - エリア: ダッシュボード上の大見出し(ライセンス / X計算機 / Y計算機)
# - サブグループ: エリア内でグラフを分けたい単位。
#   Y計算機は CPU と GPU で性質が違うため、別グラフになるようサブグループを分けている。
# - 項目: 実際のCSVカラム名
AREA_STRUCTURE = {
    "ライセンス": {
        "ライセンス": [
            "NASTRAN",
            "Abaqus",
            "LS-Dyna",
            "ADAMS",
            "Fluent",
            "Fluent-paralles",
            "Fluent-base",
        ],
    },
    "X計算機": {
        "X_CPU計算機": [f"X1_Cluster{i}" for i in range(1, 6)],
    },
    "Y計算機": {
        "Y_CPU計算機": [f"Y1_Cluster{i}" for i in range(1, 5)],
        "Y_GPU計算機": [f"Y1_GPU{i:02d}" for i in range(1, 11)],
    },
}

# 月次・年間比較(グループ単位で平均を取って比べる機能)の対象。
# ライセンスは性質の異なるソフトウェアの寄せ集めであり、
# まとめて平均しても意味を持たないためここには含めない。
COMPARISON_GROUPS = {
    "X_CPU計算機": AREA_STRUCTURE["X計算機"]["X_CPU計算機"],
    "Y_CPU計算機": AREA_STRUCTURE["Y計算機"]["Y_CPU計算機"],
    "Y_GPU計算機": AREA_STRUCTURE["Y計算機"]["Y_GPU計算機"],
}

# 逼迫とみなす閾値(ランキング表示の色分けに使用)
WARNING_THRESHOLD = 90
CAUTION_THRESHOLD = 50
