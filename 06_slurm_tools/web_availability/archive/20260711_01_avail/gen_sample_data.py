"""
動作確認用のダミーデータを data/ に生成するスクリプト。
実データを使う場合はこのファイルは不要 -- data/ に YYYYMM.csv を置くだけでよい。

  python gen_sample_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ITEMS = [
    "NASTRAN", "Abaqus", "Fluent", "CFX",
    "X1_Haswell", "X1_Broadwell", "X1_Skylake",
    "Y2_Broadwell", "Y2_Broadwell2", "Y2_Skylake",
]
rng = np.random.default_rng(0)

for ym in ["202605", "202606", "202607"]:
    year, month = int(ym[:4]), int(ym[4:])
    all_hours = pd.date_range(f"{year}-{month:02d}-01", periods=24 * 31, freq="h")
    dates = all_hours[all_hours.month == month]

    df = pd.DataFrame({"Date": dates})
    for item in ITEMS:
        base = rng.uniform(30, 60)
        # 日中(9-18時)ほど高くなる山型のパターン
        hour_effect = 25 * np.exp(-((dates.hour - 13) ** 2) / (2 * 4.5**2))
        # 平日は高め、休日は低めにする
        weekday_effect = np.where(dates.dayofweek < 5, 15, -10)
        noise = rng.normal(0, 5, len(dates))
        vals = np.clip(base + hour_effect + weekday_effect + noise, 0, 100)
        df[item] = vals.round(0).astype(int)

    df.to_csv(DATA_DIR / f"{ym}.csv", index=False)
    print(f"generated {ym}.csv ({len(df)} rows)")
