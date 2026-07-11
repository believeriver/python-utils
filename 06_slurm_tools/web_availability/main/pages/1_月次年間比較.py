import pandas as pd
import streamlit as st

from charts import annual_average_bar, monthly_comparison_bar
from components import inject_kpi_css, render_value_grid
from config import AREA_STRUCTURE, COMPARISON_GROUPS
from data_loader import list_available_years, load_year

st.set_page_config(page_title="月次・年間比較", page_icon="📈", layout="wide")
inject_kpi_css()
st.title("📈 月次・年間比較")

available_years = list_available_years()
if not available_years:
    st.info("比較用のデータがありません(data/ に複数月分のCSVを配置してください)。")
    st.stop()

c1, c2 = st.columns([1, 2])
with c1:
    compare_year = st.selectbox("対象年", available_years, index=len(available_years) - 1)
with c2:
    granularity = st.radio(
        "比較単位",
        ["計算機グループ別（CPU/GPU単位）", "項目別（クラスタ・ライセンス単位）"],
        horizontal=True,
    )

df_year = load_year(compare_year)
if df_year.empty:
    st.info(f"{compare_year}年のデータがありません。")
    st.stop()

df_year = df_year.copy()
df_year["month"] = df_year["Date"].dt.strftime("%Y-%m")

monthly_rows = []
annual_rows = []

if granularity.startswith("計算機グループ別"):
    st.caption(
        "ライセンスは性質の異なるソフトウェアの寄せ集めのため、"
        "まとめて平均する意味がないのでこの比較には含めていません。"
        "ライセンスごとの比較は「項目別」を選んでください。"
    )
    for group, cols_all in COMPARISON_GROUPS.items():
        cols = [c for c in cols_all if c in df_year.columns]
        if not cols:
            continue
        series = df_year[cols].mean(axis=1)
        tmp = pd.DataFrame({"month": df_year["month"], "value": series})
        monthly = tmp.groupby("month", as_index=False)["value"].mean()
        monthly["group"] = group
        monthly_rows.append(monthly)
        annual_rows.append({"group": group, "annual_avg": series.mean()})
else:
    # ライセンスも含め、全サブグループから比較対象を選べるようにする
    flat_groups = {
        subgroup: items
        for subgroups in AREA_STRUCTURE.values()
        for subgroup, items in subgroups.items()
    }
    target_group = st.selectbox(
        "対象グループ", list(flat_groups.keys()), key="cluster_compare_group"
    )
    cols = [c for c in flat_groups[target_group] if c in df_year.columns]
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
        monthly_comparison_bar(monthly_df, "group", f"{compare_year}年 月間平均稼働率の比較"),
        use_container_width=True,
    )

    st.subheader(f"{compare_year}年 年間平均稼働率")
    render_value_grid(dict(zip(annual_df["group"], annual_df["annual_avg"])))

    with st.expander("年間平均をグラフでも見る"):
        st.plotly_chart(
            annual_average_bar(annual_df, "group", f"{compare_year}年 年間平均稼働率ランキング"),
            use_container_width=True,
        )
