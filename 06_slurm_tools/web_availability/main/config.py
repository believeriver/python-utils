# クラスタ/ライセンスの構成(どのエリア・サブグループにどの項目があるか)は
# assets.csv(台帳)から期間ごとに動的に組み立てる。詳細は assets.py を参照。
# config.py には期間に依存しない設定のみを置く。

# 逼迫とみなす閾値(ランキング表示・KPIカードの色分けに使用)
WARNING_THRESHOLD = 90
CAUTION_THRESHOLD = 50
