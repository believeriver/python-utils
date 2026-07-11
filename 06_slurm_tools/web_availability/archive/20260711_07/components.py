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
    """カードグリッド用のCSSを注入する。カードを使うページの先頭で1回呼ぶ。

    色は固定値ではなく Streamlit のテーマ変数(--background-color 等)を使う。
    これにより、config.toml の Light テーマ時はもちろん、
    ユーザーが右上メニューから Dark に切り替えた場合も自動的に馴染む配色になる。
    """
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
            background: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-left: 4px solid #a0cbe8;
            border-radius: 8px;
            padding: 10px 14px;
        }
        .kpi-name {
            font-size: 0.78rem;
            color: var(--text-color);
            opacity: 0.65;
            font-weight: 600;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-color);
            line-height: 1.2;
        }
        .kpi-delta {
            font-size: 0.78rem;
            font-weight: 600;
            margin-top: 2px;
        }
        .kpi-avg {
            opacity: 0.6;
            font-weight: 400;
        }
        .area-header {
            border-left: 5px solid var(--primary-color);
            padding: 4px 0 4px 14px;
            margin: 30px 0 14px 0;
        }
        .area-header span {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_area_header(text: str) -> None:
    """エリア見出し(左にアクセントバー付き)を表示する"""
    st.markdown(f'<div class="area-header"><span>{text}</span></div>', unsafe_allow_html=True)


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
