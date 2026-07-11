"""
計算機・ライセンスの「台帳」を扱うモジュール。

クラスタやライセンスは年々増設・廃止されるため、config.py に
固定リストとして書くのではなく、assets.csv (開始日・終了日つきの台帳)から
「指定した期間に実際に稼働していた項目」を動的に組み立てる。

assets.csv の管理方法:
- 増設したら行を1つ追加する(start_date = 稼働開始日、end_date は空)
- 廃止したら該当行の end_date に廃止日を入れる
- コードは変更不要
"""
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ASSETS_PATH = Path(__file__).parent / "assets.csv"


@st.cache_data(ttl=300, show_spinner=False)
def load_assets() -> pd.DataFrame:
    df = pd.read_csv(ASSETS_PATH, parse_dates=["start_date", "end_date"])
    return df


def _active_mask(df: pd.DataFrame, start: date, end: date) -> pd.Series:
    """[start_date, end_date] の期間が [start, end] と少しでも重なっているかを判定する

    end_date が空(NaT)の項目は「現在も稼働中」として扱う。
    """
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    started_before_period_end = df["start_date"] <= end_ts
    not_yet_retired_at_period_start = df["end_date"].isna() | (df["end_date"] >= start_ts)
    return started_before_period_end & not_yet_retired_at_period_start


def area_structure_for_period(start: date, end: date) -> dict:
    """指定期間に稼働していた項目だけで area -> subgroup -> [item_id] を組み立てる"""
    df = load_assets()
    active = df.loc[_active_mask(df, start, end)]
    structure: dict = {}
    for area, area_df in active.groupby("area", sort=False):
        structure[area] = {}
        for subgroup, sub_df in area_df.groupby("subgroup", sort=False):
            structure[area][subgroup] = sub_df["item_id"].tolist()
    return structure


def comparison_groups_for_period(start: date, end: date) -> dict:
    """月次・年間比較(グループ単位平均)の対象となる項目(category=cluster)だけを返す

    ライセンスは性質の異なるソフトの寄せ集めで平均する意味がないため、
    category="cluster" の項目のみを対象にしている。
    """
    df = load_assets()
    active = df.loc[_active_mask(df, start, end) & (df["category"] == "cluster")]
    return {
        subgroup: sub_df["item_id"].tolist()
        for subgroup, sub_df in active.groupby("subgroup", sort=False)
    }


def retired_or_added_in_period(start: date, end: date) -> pd.DataFrame:
    """指定期間中に「新規稼働開始」または「廃止」があった項目の一覧(参考表示用)"""
    df = load_assets()
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    added = (df["start_date"] >= start_ts) & (df["start_date"] <= end_ts)
    retired = df["end_date"].notna() & (df["end_date"] >= start_ts) & (df["end_date"] <= end_ts)
    return df.loc[added | retired, ["item_id", "area", "subgroup", "start_date", "end_date"]]
