from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import WARNING_THRESHOLD, CAUTION_THRESHOLD

TEMPLATE = "plotly_white"
COLOR_SEQ = px.colors.qualitative.Set2


def _status_color(value: float) -> str:
    """稼働率の高さに応じた色(逼迫=赤、通常=青、余裕あり=水色)"""
    if value >= WARNING_THRESHOLD:
        return "#e15759"
    if value >= CAUTION_THRESHOLD:
        return "#4e79a7"
    return "#a0cbe8"


def line_chart(df: pd.DataFrame, items: list[str], title: str) -> go.Figure:
    """期間内の稼働率推移(複数項目を折れ線で重ね描き)"""
    fig = go.Figure()
    for i, item in enumerate(items):
        if item not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df[item],
                mode="lines",
                name=item,
                line=dict(width=1.6, color=COLOR_SEQ[i % len(COLOR_SEQ)]),
                hovertemplate="%{y:.0f}%<extra>" + item + "</extra>",
            )
        )
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left"),
        template=TEMPLATE,
        height=440,
        yaxis=dict(title="稼働率 (%)", range=[0, 100]),
        xaxis=dict(title=None, rangeslider=dict(visible=True), rangeslider_thickness=0.08),
        legend=dict(orientation="h", yanchor="top", y=-0.35, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=50, b=110),
        hovermode="x unified",
    )
    return fig


def heatmap(df: pd.DataFrame, item: str, title: str) -> go.Figure:
    """曜日(日付)× 時間帯で稼働率パターンを見るヒートマップ"""
    d = df[["Date", item]].copy()
    d["day"] = d["Date"].dt.strftime("%m/%d (%a)")
    d["hour"] = d["Date"].dt.hour
    pivot = d.pivot_table(index="day", columns="hour", values=item, aggfunc="mean")

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[f"{h}:00" for h in pivot.columns],
            y=pivot.index,
            colorscale="YlGnBu",
            zmin=0,
            zmax=100,
            colorbar=dict(title="%"),
            hovertemplate="日: %{y}<br>時: %{x}<br>稼働率: %{z:.0f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        template=TEMPLATE,
        height=max(420, 22 * len(pivot.index)),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def ranking_bar(df: pd.DataFrame, items: list[str], title: str) -> go.Figure:
    """平均稼働率が高い順のランキング(逼迫度で色分け)"""
    means = {item: df[item].mean() for item in items if item in df.columns}
    s = pd.Series(means).sort_values()

    colors = [_status_color(v) for v in s.values]

    fig = go.Figure(
        go.Bar(
            x=s.values,
            y=s.index,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}%" for v in s.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=title,
        template=TEMPLATE,
        height=90 + 42 * len(s),
        xaxis=dict(title="平均稼働率 (%)", range=[0, 108]),
        margin=dict(l=10, r=30, t=60, b=10),
    )
    return fig


def latest_snapshot_bar(df: pd.DataFrame, items: list[str], title: str) -> go.Figure:
    """最新時刻の稼働率を、リストの並び順のまま横棒グラフで表示する

    ranking_bar とは違い、平均値で並び替えず、サイドバーで選んだ順序をそのまま使う。
    """
    latest_row = df.iloc[-1]
    latest_time = df["Date"].iloc[-1]
    valid_items = [i for i in items if i in df.columns]
    values = [latest_row[i] for i in valid_items]

    # 横棒グラフは配列の先頭が下に来るため、リストの先頭が上に来るよう逆順にして渡す
    y = list(reversed(valid_items))
    x = list(reversed(values))

    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            orientation="h",
            marker_color=[_status_color(v) for v in x],
            text=[f"{v:.0f}%" for v in x],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"{title}（{latest_time:%Y-%m-%d %H:%M} 時点）",
        template=TEMPLATE,
        height=90 + 42 * len(valid_items),
        xaxis=dict(title="稼働率 (%)", range=[0, 108]),
        margin=dict(l=10, r=30, t=60, b=10),
    )
    return fig


def monthly_comparison_bar(
    monthly_df: pd.DataFrame,
    group_col: str,
    title: str,
    x_col: str = "month",
    category_orders: dict | None = None,
) -> go.Figure:
    """value, <group_col>, <x_col> の列を持つDataFrameから月次比較の棒グラフを作る

    エリア単位・項目(クラスタ)単位のどちらでも、事前に
    value(平均稼働率) / group_col(比較対象名) / x_col(横軸のラベル)
    に整形しておけば共通で使える。
    """
    fig = px.bar(
        monthly_df,
        x=x_col,
        y="value",
        color=group_col,
        barmode="group",
        template=TEMPLATE,
        color_discrete_sequence=COLOR_SEQ,
        category_orders=category_orders,
    )
    fig.update_traces(hovertemplate="%{y:.1f}%<extra>%{fullData.name}</extra>")
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left"),
        yaxis=dict(title="平均稼働率 (%)", range=[0, 100]),
        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="left", x=0, title=None),
        margin=dict(l=10, r=10, t=50, b=90),
        height=420,
    )
    # カテゴリ軸は項目数が多いとPlotlyが自動的にラベルを間引くことがあるため、
    # 全ての月の目盛りを強制的に表示する
    fig.update_xaxes(title=None, type="category", tickmode="linear", dtick=1)
    return fig


def annual_average_bar(annual_df: pd.DataFrame, group_col: str, title: str) -> go.Figure:
    """group_col, annual_avg の列を持つDataFrameから年間平均の棒グラフを作る"""
    s = annual_df.set_index(group_col)["annual_avg"].sort_values()

    fig = go.Figure(
        go.Bar(
            x=s.values,
            y=s.index,
            orientation="h",
            marker_color=[_status_color(v) for v in s.values],
            text=[f"{v:.1f}%" for v in s.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=title,
        template=TEMPLATE,
        height=90 + 42 * len(s),
        xaxis=dict(title="年間平均稼働率 (%)", range=[0, 108]),
        margin=dict(l=10, r=30, t=60, b=10),
    )
    return fig
