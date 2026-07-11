"""
月次CSV(YYYYMM.csv)を読み込むレイヤー。

想定フォーマット:
    Date,NASTRAN,Abaqus,FLUENT,Cluster01,Cluster02, ...
    2025-05-01 00:00:00,63,80,80,36,19, ...

- 1ファイル = 1ヶ月分、1時間ごとのレコード
- data/ ディレクトリに YYYYMM.csv を置いておくだけで自動的に読み込み対象になる
"""
import glob
import os
from datetime import date

import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def list_available_months() -> list[str]:
    """data/ 配下にある YYYYMM.csv の一覧(YYYYMM文字列)を返す"""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    months = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        if len(name) == 6 and name.isdigit():
            months.append(name)
    return months


@st.cache_data(ttl=300, show_spinner=False)
def _load_month_csv(yyyymm: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{yyyymm}.csv")
    df = pd.read_csv(path, parse_dates=["Date"])
    return df


@st.cache_data(ttl=300, show_spinner="データを読み込み中...")
def load_range(start: date, end: date) -> pd.DataFrame:
    """指定期間をカバーする月次CSVを必要な分だけ読み込み、結合してフィルタする"""
    months = pd.period_range(start, end, freq="M")
    frames = []
    for p in months:
        yyyymm = p.strftime("%Y%m")
        path = os.path.join(DATA_DIR, f"{yyyymm}.csv")
        if os.path.exists(path):
            frames.append(_load_month_csv(yyyymm))

    if not frames:
        return pd.DataFrame(columns=["Date"])

    df = pd.concat(frames, ignore_index=True)
    mask = (df["Date"] >= pd.Timestamp(start)) & (
        df["Date"] < pd.Timestamp(end) + pd.Timedelta(days=1)
    )
    return df.loc[mask].sort_values("Date").reset_index(drop=True)
