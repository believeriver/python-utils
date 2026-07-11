from datetime import date, timedelta

import pandas as pd
import streamlit as st

from charts import annual_average_bar, heatmap, line_chart, monthly_comparison_bar, ranking_bar
from config import AREA_GROUPS
from data_loader import list_available_years, load_range, load_year

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
    /* テーマがダークモードでも文字色が白に飛ばないよう明示指定 */
    [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #1f2933 !important;
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

    st.subheader("期間")
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
    st.subheader("表示項目")
    # エリアごとに項目選択(元dashboard.pyの selected-license / selected-nagasaki 等に相当)
    selections = {}
    for area, items in AREA_GROUPS.items():
        with st.expander(area, expanded=True):
            selections[area] = st.multiselect(
                "項目", items, default=items, key=f"select_{area}", label_visibility="collapsed"
            )

    st.divider()
    auto_refresh = st.checkbox("30秒ごとに自動更新", value=False)
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh

            st_autorefresh(interval=30_000, key="refresh")
        except ImportError:
            st.warning("`pip install streamlit-autorefresh` が必要です")

# ---------------- データ読み込み(全エリア共通) ----------------
df = load_range(start_date, end_date)

if df.empty:
    st.info("該当期間のデータが見つかりません。data/ に YYYYMM.csv を配置してください。")
    st.stop()

# ---------------- エリアごとにブロックを縦に並べて表示 ----------------
for area, items in AREA_GROUPS.items():
    selected_items = selections[area]
    available_items = [i for i in selected_items if i in df.columns]

    st.subheader(f"■ {area}")

    if not available_items:
        st.info("表示する項目がありません。サイドバーで項目を選択してください。")
        st.divider()
        continue

    # KPIサマリ
    latest = df.iloc[-1]
    cols = st.columns(len(available_items))
    for c, item in zip(cols, available_items):
        current = latest[item]
        avg = df[item].mean()
        c.metric(item, f"{current:.0f}%", f"平均 {avg:.1f}%")

    # トレンドグラフ
    st.plotly_chart(
        line_chart(df, available_items, f"{area} 稼働率の推移（{start_date} 〜 {end_date}）"),
        use_container_width=True,
    )

    # ヒートマップ & ランキングは折りたたみに格納(3エリア分を全部開くと縦に長くなりすぎるため)
    with st.expander(f"🔍 {area} の詳細(時間帯パターン・ランキング)"):
        tab1, tab2 = st.tabs(["🗓 時間帯ヒートマップ", "🏆 平均稼働率ランキング"])
        with tab1:
            heat_item = st.selectbox("表示する項目", available_items, key=f"heat_{area}")
            st.plotly_chart(
                heatmap(df, heat_item, f"{heat_item} 曜日×時間帯の稼働率パターン"),
                use_container_width=True,
            )
        with tab2:
            st.plotly_chart(
                ranking_bar(df, available_items, f"{area} 平均稼働率ランキング"),
                use_container_width=True,
            )

    st.divider()

# ---------------- 月次・年間比較 ----------------
st.header("📊 月次・年間比較")

available_years = list_available_years()
if not available_years:
    st.info("比較用のデータがありません(data/ に複数月分のCSVを配置してください)。")
else:
    c1, c2 = st.columns([1, 2])
    with c1:
        compare_year = st.selectbox("対象年", available_years, index=len(available_years) - 1)
    with c2:
        granularity = st.radio(
            "比較単位", ["エリア別（地区単位）", "項目別（クラスタ単位）"], horizontal=True
        )

    df_year = load_year(compare_year)

    if df_year.empty:
        st.info(f"{compare_year}年のデータがありません。")
    else:
        df_year = df_year.copy()
        df_year["month"] = df_year["Date"].dt.strftime("%Y-%m")

        monthly_rows = []
        annual_rows = []

        if granularity == "エリア別（地区単位）":
            # エリア内の項目を平均してから、そのエリアの月次・年間平均を出す
            for area, items in AREA_GROUPS.items():
                cols = [c for c in items if c in df_year.columns]
                if not cols:
                    continue
                area_series = df_year[cols].mean(axis=1)
                tmp = pd.DataFrame({"month": df_year["month"], "value": area_series})
                monthly = tmp.groupby("month", as_index=False)["value"].mean()
                monthly["group"] = area
                monthly_rows.append(monthly)
                annual_rows.append({"group": area, "annual_avg": area_series.mean()})
        else:
            target_area = st.selectbox(
                "対象エリア", list(AREA_GROUPS.keys()), key="cluster_compare_area"
            )
            cols = [c for c in AREA_GROUPS[target_area] if c in df_year.columns]
            for item in cols:
                tmp = pd.DataFrame({"month": df_year["month"], "value": df_year[item]})
                monthly = tmp.groupby("month", as_index=False)["value"].mean()
                monthly["group"] = item
                monthly_rows.append(monthly)
                annual_rows.append({"group": item, "annual_avg": df_year[item].mean()})

        if not monthly_rows:
            st.info("表示できるデータがありません。")
        else:
            monthly_df = pd.concat(monthly_rows, ignore_index=True)
            annual_df = pd.DataFrame(annual_rows)

            st.plotly_chart(
                monthly_comparison_bar(
                    monthly_df, "group", f"{compare_year}年 月間平均稼働率の比較"
                ),
                use_container_width=True,
            )

            st.subheader(f"{compare_year}年 年間平均稼働率")
            m_cols = st.columns(len(annual_df))
            for c, row in zip(m_cols, annual_df.itertuples()):
                c.metric(row.group, f"{row.annual_avg:.1f}%")

            with st.expander("年間平均をグラフでも見る"):
                st.plotly_chart(
                    annual_average_bar(
                        annual_df, "group", f"{compare_year}年 年間平均稼働率ランキング"
                    ),
                    use_container_width=True,
                )

st.divider()

# ---------------- 生データ / ダウンロード(全エリア横断) ----------------
all_selected = []
for area, items in AREA_GROUPS.items():
    for item in selections[area]:
        if item in df.columns and item not in all_selected:
            all_selected.append(item)

with st.expander("📄 生データを見る / ダウンロード"):
    show_cols = ["Date"] + all_selected
    st.dataframe(df[show_cols], use_container_width=True, height=300)
    csv = df[show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSVダウンロード",
        csv,
        file_name=f"utilization_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
