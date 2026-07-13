"""
動作確認用のダミーデータを data/ に生成するスクリプト。
実データを使う場合はこのファイルは不要 -- data/ に YYYYMM.csv を置くだけでよい。

assets.csv(台帳)の start_date/end_date を見て、その月に実際に稼働していた
項目だけをCSVに列として出力する(クラスタの増設・廃止をシミュレートしている)。

  python gen_sample_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

assets = pd.read_csv(Path(__file__).parent / "assets.csv", parse_dates=["start_date", "end_date"])

rng = np.random.default_rng(0)

# 2025年1月〜2026年7月分をまとめて生成する
months = pd.period_range("2025-01", "2026-07", freq="M")

for period in months:
    year, month = period.year, period.month
    month_start = pd.Timestamp(year=year, month=month, day=1)
    month_end = month_start + pd.offsets.MonthEnd(0)

    # その月に稼働していた項目だけを台帳から抽出(増設/廃止をシミュレート)
    active = assets[
        (assets["start_date"] <= month_end)
        & (assets["end_date"].isna() | (assets["end_date"] >= month_start))
    ]
    items = active["item_id"].tolist()

    all_hours = pd.date_range(f"{year}-{month:02d}-01", periods=24 * 31, freq="h")
    dates = all_hours[all_hours.month == month]

    df = pd.DataFrame({"Date": dates})
    for item in items:
        base = rng.uniform(30, 60)
        gpu_offset = 15 if "GPU" in item else 0
        season_effect = 10 * np.sin((month - 3) / 12 * 2 * np.pi)
        hour_effect = 25 * np.exp(-((dates.hour - 13) ** 2) / (2 * 4.5**2))
        weekday_effect = np.where(dates.dayofweek < 5, 15, -10)
        noise = rng.normal(0, 5, len(dates))
        vals = np.clip(base + gpu_offset + season_effect + hour_effect + weekday_effect + noise, 0, 100)
        df[item] = vals.round(0).astype(int)

    ym = f"{year}{month:02d}"
    df.to_csv(DATA_DIR / f"{ym}.csv", index=False)
    print(f"generated {ym}.csv ({len(df)} rows, {len(items)} items)")
