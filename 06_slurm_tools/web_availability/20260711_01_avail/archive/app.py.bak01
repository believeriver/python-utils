from datetime import date, timedelta

import streamlit as st

from charts import heatmap, line_chart, ranking_bar
from config import AREA_GROUPS
from data_loader import load_range

st.set_page_config(page_title="稼働率モニタリング", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background: #f7f9fb;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 12px 16px;
    }
    div.block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 並列計算機・ライセンス稼働率ダッシュボード")

# ---------------- サイドバー ----------------
with st.sidebar:
    st.header("表示設定")

    area = st.radio("対象", list(AREA_GROUPS.keys()))
    all_items = AREA_GROUPS[area]
    selected_items = st.multiselect("項目", all_items, default=all_items)

    st.divider()
    period_mode = st.radio("期間", ["直近24時間", "直近7日間", "直近30日間", "期間を指定"], index=1)

    today = date.today()
    if period_mode == "直近24時間":
        start_date, end_date = today - timedelta(days=1), today
    elif period_mode == "直近7日間":
        start_date, end_date = today - timedelta(days=7), today
    elif period_mode == "直近30日間":
        start_date, end_date = today - timedelta(days=30), today
    else:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("開始日", today - timedelta(days=30))
        end_date = c2.date_input("終了日", today)

    st.divider()
    auto_refresh = st.checkbox("30秒ごとに自動更新", value=False)
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh

            st_autorefresh(interval=30_000, key="refresh")
        except ImportError:
            st.warning("`pip install streamlit-autorefresh` が必要です")

# ---------------- データ読み込み ----------------
df = load_range(start_date, end_date)

if df.empty:
    st.info("該当期間のデータが見つかりません。data/ に YYYYMM.csv を配置してください。")
    st.stop()
if not selected_items:
    st.info("表示する項目を選択してください。")
    st.stop()

available_items = [i for i in selected_items if i in df.columns]

# ---------------- KPIサマリ ----------------
latest = df.iloc[-1]
cols = st.columns(len(available_items))
for c, item in zip(cols, available_items):
    current = latest[item]
    avg = df[item].mean()
    c.metric(item, f"{current:.0f}%", f"平均 {avg:.1f}%")

st.divider()

# ---------------- トレンドグラフ ----------------
st.plotly_chart(
    line_chart(df, available_items, f"{area} 稼働率の推移（{start_date} 〜 {end_date}）"),
    use_container_width=True,
)

# ---------------- ヒートマップ & ランキング ----------------
tab1, tab2 = st.tabs(["🗓 時間帯ヒートマップ", "🏆 平均稼働率ランキング"])

with tab1:
    heat_item = st.selectbox("表示する項目", available_items)
    st.plotly_chart(
        heatmap(df, heat_item, f"{heat_item} 曜日×時間帯の稼働率パターン"),
        use_container_width=True,
    )

with tab2:
    st.plotly_chart(
        ranking_bar(df, available_items, f"{area} 平均稼働率ランキング"),
        use_container_width=True,
    )

# ---------------- 生データ / ダウンロード ----------------
with st.expander("📄 生データを見る / ダウンロード"):
    show_cols = ["Date"] + available_items
    st.dataframe(df[show_cols], use_container_width=True, height=300)
    csv = df[show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSVダウンロード",
        csv,
        file_name=f"utilization_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
