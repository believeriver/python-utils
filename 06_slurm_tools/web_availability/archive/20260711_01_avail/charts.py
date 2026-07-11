import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import WARNING_THRESHOLD, CAUTION_THRESHOLD

TEMPLATE = "plotly_white"
COLOR_SEQ = px.colors.qualitative.Set2


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

    def _color(v: float) -> str:
        if v >= WARNING_THRESHOLD:
            return "#e15759"
        if v >= CAUTION_THRESHOLD:
            return "#4e79a7"
        return "#a0cbe8"

    colors = [_color(v) for v in s.values]

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