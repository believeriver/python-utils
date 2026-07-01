"""
ネットワーク監視ツール - メインページ
"""

import streamlit as st

st.set_page_config(
    page_title="ネットワーク監視",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)



# ---------------------------------------------------------------------------
# VLAN 定義（実環境に合わせて編集してください）
# ---------------------------------------------------------------------------

VLAN_LIST = [
    {"VLAN ID": 10,  "ネットワーク名": "業務系 A棟",       "用途": "一般業務PC・プリンター",         "帯域": "1 Gbps"},
    {"VLAN ID": 20,  "ネットワーク名": "業務系 B棟",       "用途": "一般業務PC・プリンター",         "帯域": "1 Gbps"},
    {"VLAN ID": 30,  "ネットワーク名": "研究系",           "用途": "ワークステーション・計算サーバー", "帯域": "10 Gbps"},
    {"VLAN ID": 40,  "ネットワーク名": "管理系",           "用途": "ネットワーク機器・サーバー管理",  "帯域": "1 Gbps"},
    {"VLAN ID": 100, "ネットワーク名": "サーバーセグメント","用途": "ファイルサーバー・認証サーバー",  "帯域": "10 Gbps"},
]


# ---------------------------------------------------------------------------
# ページ本体
# ---------------------------------------------------------------------------

st.title("🖥️ ネットワーク監視ツール")
st.caption("社内ネットワークの接続状況を確認するためのツールです。")

st.divider()

# ---- 使い方 ----
st.subheader("📖 使い方")

col1, col2, col3 = st.columns(3)

with col1:
    st.info(
        "**① 左メニューを選択**\n\n"
        "画面左のサイドバーから\n"
        "確認したい機能を選んでください。"
    )
with col2:
    st.info(
        "**② フィルタで絞り込み**\n\n"
        "VLANやIPアドレスで絞り込むと\n"
        "目的の機器をすばやく見つけられます。"
    )
with col3:
    st.info(
        "**③ CSVで書き出し**\n\n"
        "「CSVダウンロード」ボタンから\n"
        "Excelで開ける形式で保存できます。"
    )

st.divider()

# ---- 機能一覧 ----
st.subheader("🗂️ 機能一覧")

st.markdown("""
| ページ | 内容 | 更新タイミング |
|--------|------|--------------|
| 🔍 ARP確認 | 各VLANに接続中の機器（IPアドレス・MACアドレス）を一覧表示 | ページを開いたとき（60秒キャッシュ） |
""")

st.divider()

# ---- VLAN 一覧 ----
st.subheader("🌐 VLANとネットワーク構成")
st.caption("社内ネットワークは用途ごとに以下のVLANに分かれています。")

import pandas as pd
df_vlan = pd.DataFrame(VLAN_LIST)

st.dataframe(
    df_vlan,
    use_container_width=True,
    hide_index=True,
    column_config={
        "VLAN ID": st.column_config.NumberColumn("VLAN ID", format="%d", width="small"),
        "ネットワーク名": st.column_config.TextColumn("ネットワーク名", width="medium"),
        "用途":          st.column_config.TextColumn("用途",          width="large"),
        "帯域":          st.column_config.TextColumn("帯域",          width="small"),
    },
)

st.divider()

# ---- 注意事項 ----
st.subheader("⚠️ ご利用にあたって")

st.warning(
    "- このツールはネットワーク機器への読み取り専用アクセスを行います。設定変更はできません。\n"
    "- 表示される情報は取得時点のものです。リアルタイムの変化は「再取得」ボタンで更新してください。\n"
    "- 不明な点はネットワーク管理者（情報システム担当）までお問い合わせください。"
)

# ---- フッター ----
st.divider()
st.caption("Network Monitor v1.0　／　管理: 情報システム部門")