from datetime import date, timedelta

import pandas as pd
import streamlit as st

from assets import area_structure_for_period, retired_or_added_in_period
from charts import heatmap, latest_snapshot_bar, line_chart, ranking_bar
from components import inject_kpi_css, render_area_header, render_kpi_grid
from data_loader import load_range

st.set_page_config(page_title="稼働率モニタリング", page_icon="📊", layout="wide")

inject_kpi_css()
st.markdown(
    """
    <style>
    div.block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 並列計算機・ライセンス稼働率ダッシュボード")
st.caption("月次・年間の比較は左のナビゲーションの「月次年間比較」ページをご覧ください。")

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

    # 選択された期間に「実際に稼働していた」項目だけを台帳(assets.csv)から組み立てる。
    # クラスタの増設・廃止があっても、ここを直接編集する必要はない。
    area_structure = area_structure_for_period(start_date, end_date)
    subgroups_flat = [
        (area, subgroup, items)
        for area, subgroups in area_structure.items()
        for subgroup, items in subgroups.items()
    ]

    st.divider()
    st.subheader("表示項目")
    selections = {}
    for area, subgroup, items in subgroups_flat:
        label = f"{area} - {subgroup}" if subgroup != area else area
        # 期間が変わると対象項目の顔ぶれも変わりうるため、期間もキーに含めて
        # 前回選択の残骸(廃止済み項目など)を引きずらないようにする
        widget_key = f"select_{subgroup}_{start_date.isoformat()}_{end_date.isoformat()}"
        with st.expander(label, expanded=True):
            selections[subgroup] = st.multiselect(
                "項目", items, default=items, key=widget_key, label_visibility="collapsed"
            )

    st.divider()
    auto_refresh = st.checkbox("30秒ごとに自動更新", value=False)
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh

            st_autorefresh(interval=30_000, key="refresh")
        except ImportError:
            st.warning("`pip install streamlit-autorefresh` が必要です")

# ---------------- データ読み込み(全体共通) ----------------
df = load_range(start_date, end_date)

if df.empty:
    st.info("該当期間のデータが見つかりません。data/ に YYYYMM.csv を配置してください。")
    st.stop()

if not area_structure:
    st.info("この期間に稼働していた項目が assets.csv に見つかりません。")
    st.stop()

# 期間中に増設・廃止があれば知らせる(構成変更の見落とし防止)
changes = retired_or_added_in_period(start_date, end_date)
if not changes.empty:
    with st.expander(f"ℹ️ この期間中に構成変更がありました({len(changes)}件)"):
        for row in changes.itertuples():
            if pd.notna(row.end_date):
                st.write(f"🔻 {row.item_id}（{row.subgroup}）: {row.end_date.date()} に廃止")
            else:
                st.write(f"🔺 {row.item_id}（{row.subgroup}）: {row.start_date.date()} に稼働開始")

# ---------------- エリア → サブグループの順に表示 ----------------
for area, subgroups in area_structure.items():
    render_area_header(area)

    for subgroup, items in subgroups.items():
        selected_items = selections[subgroup]
        available_items = [i for i in selected_items if i in df.columns]

        with st.container(border=True):
            st.subheader(f"■ {subgroup}")

            if not available_items:
                st.info("表示する項目がありません。サイドバーで項目を選択してください。")
                continue

            # KPIサマリ(現在値・期間平均との差分をカードグリッドで表示)
            render_kpi_grid(df, available_items)

            # トレンドグラフ
            st.plotly_chart(
                line_chart(df, available_items, f"{subgroup} 稼働率の推移（{start_date} 〜 {end_date}）"),
                use_container_width=True,
            )

            # ヒートマップ & ランキング & 最新スナップショットは折りたたみに格納
            with st.expander(f"🔍 {subgroup} の詳細(時間帯パターン・ランキング・最新値)"):
                tab1, tab2, tab3 = st.tabs(
                    ["🗓 時間帯ヒートマップ", "🏆 平均稼働率ランキング", "⏱ 最新時間の稼働率"]
                )
                with tab1:
                    heat_item = st.selectbox("表示する項目", available_items, key=f"heat_{subgroup}")
                    st.plotly_chart(
                        heatmap(df, heat_item, f"{heat_item} 曜日×時間帯の稼働率パターン"),
                        use_container_width=True,
                    )
                with tab2:
                    st.plotly_chart(
                        ranking_bar(df, available_items, f"{subgroup} 平均稼働率ランキング"),
                        use_container_width=True,
                    )
                with tab3:
                    st.plotly_chart(
                        latest_snapshot_bar(df, available_items, f"{subgroup} 最新時間の稼働率"),
                        use_container_width=True,
                    )

# ---------------- 生データ / ダウンロード(全体横断) ----------------
all_selected = []
for _, subgroup, _ in subgroups_flat:
    for item in selections[subgroup]:
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
