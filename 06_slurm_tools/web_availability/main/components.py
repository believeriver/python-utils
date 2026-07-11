"""
KPIサマリーをカードのグリッドで表示するコンポーネント。

st.columns(N) で横一列に並べる方式は、項目数が増える(GPU10台など)と
画面幅に収まらず見づらくなるため、CSS Grid(auto-fill)で
自動的に折り返すカードレイアウトにしている。
"""
import pandas as pd
import streamlit as st

from config import CAUTION_THRESHOLD, WARNING_THRESHOLD


def inject_kpi_css() -> None:
    """カードグリッド用のCSSを注入する。カードを使うページの先頭で1回呼ぶ。"""
    st.markdown(
        """
        <style>
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin: 10px 0 20px 0;
        }
        .kpi-card {
            background: #f7f9fb;
            border: 1px solid #e6e9ef;
            border-left: 4px solid #a0cbe8;
            border-radius: 8px;
            padding: 10px 14px;
        }
        .kpi-name {
            font-size: 0.78rem;
            color: #5b6672;
            font-weight: 600;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1f2933;
            line-height: 1.2;
        }
        .kpi-delta {
            font-size: 0.78rem;
            font-weight: 600;
            margin-top: 2px;
        }
        .kpi-avg {
            color: #8a94a0;
            font-weight: 400;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_color(value: float) -> str:
    if value >= WARNING_THRESHOLD:
        return "#e15759"  # 逼迫(赤)
    if value >= CAUTION_THRESHOLD:
        return "#4e79a7"  # 通常(青)
    return "#a0cbe8"  # 余裕あり(水色)


def render_kpi_grid(df: pd.DataFrame, items: list[str]) -> None:
    """現在値・期間平均・差分をカードグリッドで表示する(現在値の高さで色帯を変える)"""
    latest = df.iloc[-1]
    cards = []
    for item in items:
        current = latest[item]
        avg = df[item].mean()
        diff = current - avg
        arrow = "▲" if diff >= 0 else "▼"
        delta_color = "#2f9e44" if diff >= 0 else "#e03131"
        cards.append(
            f"""<div class="kpi-card" style="border-left-color:{_status_color(current)};">
                <div class="kpi-name" title="{item}">{item}</div>
                <div class="kpi-value">{current:.0f}%</div>
                <div class="kpi-delta" style="color:{delta_color};">
                    {arrow} {diff:+.1f}pt <span class="kpi-avg">(平均{avg:.1f}%)</span>
                </div>
            </div>"""
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_value_grid(labels_values: dict, unit: str = "%") -> None:
    """ラベルと単一の値だけを並べたい場合(年間平均など)のカードグリッド"""
    cards = []
    for label, value in labels_values.items():
        cards.append(
            f"""<div class="kpi-card" style="border-left-color:{_status_color(value)};">
                <div class="kpi-name" title="{label}">{label}</div>
                <div class="kpi-value">{value:.1f}{unit}</div>
            </div>"""
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
