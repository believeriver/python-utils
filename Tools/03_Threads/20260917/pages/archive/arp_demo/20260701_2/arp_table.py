"""
ARPテーブル確認 - デモ版（ダミーデータ使用）
- YAML認証（streamlit-authenticator 新API対応）
- SNMPの代わりにダミーデータでUIを確認可能
- 本番移行時は fetch_arp_dataframe() 内を実SNMP呼び出しに差し替える
"""

from __future__ import annotations
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.yaml"


# ---------------------------------------------------------------------------
# ダミーARPデータ（本番では SNMP 取得に差し替え）
# ---------------------------------------------------------------------------

DUMMY_ARP: list[dict] = [
    # Core-SW1
    {"スイッチ": "Core-SW1", "VLAN": 10,  "インターフェース": "Vlan10",  "IPアドレス": "10.0.10.1",   "MACアドレス": "00:1a:2b:3c:4d:01"},
    {"スイッチ": "Core-SW1", "VLAN": 10,  "インターフェース": "Vlan10",  "IPアドレス": "10.0.10.101", "MACアドレス": "00:1a:2b:3c:4d:02"},
    {"スイッチ": "Core-SW1", "VLAN": 10,  "インターフェース": "Vlan10",  "IPアドレス": "10.0.10.102", "MACアドレス": "00:1a:2b:3c:4d:03"},
    {"スイッチ": "Core-SW1", "VLAN": 20,  "インターフェース": "Vlan20",  "IPアドレス": "10.0.20.1",   "MACアドレス": "00:aa:bb:cc:dd:01"},
    {"スイッチ": "Core-SW1", "VLAN": 20,  "インターフェース": "Vlan20",  "IPアドレス": "10.0.20.50",  "MACアドレス": "00:aa:bb:cc:dd:02"},
    {"スイッチ": "Core-SW1", "VLAN": 20,  "インターフェース": "Vlan20",  "IPアドレス": "10.0.20.51",  "MACアドレス": "00:aa:bb:cc:dd:03"},
    {"スイッチ": "Core-SW1", "VLAN": 30,  "インターフェース": "Vlan30",  "IPアドレス": "10.0.30.1",   "MACアドレス": "a0:b0:c0:d0:e0:01"},
    {"スイッチ": "Core-SW1", "VLAN": 100, "インターフェース": "Vlan100", "IPアドレス": "172.16.100.1", "MACアドレス": "11:22:33:44:55:01"},
    {"スイッチ": "Core-SW1", "VLAN": 100, "インターフェース": "Vlan100", "IPアドレス": "172.16.100.2", "MACアドレス": "11:22:33:44:55:02"},
    # Core-SW2
    {"スイッチ": "Core-SW2", "VLAN": 10,  "インターフェース": "Vlan10",  "IPアドレス": "10.0.10.201", "MACアドレス": "cc:dd:ee:ff:00:01"},
    {"スイッチ": "Core-SW2", "VLAN": 10,  "インターフェース": "Vlan10",  "IPアドレス": "10.0.10.202", "MACアドレス": "cc:dd:ee:ff:00:02"},
    {"スイッチ": "Core-SW2", "VLAN": 40,  "インターフェース": "Vlan40",  "IPアドレス": "192.168.40.1","MACアドレス": "fe:dc:ba:98:76:01"},
    {"スイッチ": "Core-SW2", "VLAN": 40,  "インターフェース": "Vlan40",  "IPアドレス": "192.168.40.10","MACアドレス": "fe:dc:ba:98:76:02"},
    {"スイッチ": "Core-SW2", "VLAN": 100, "インターフェース": "Vlan100", "IPアドレス": "172.16.100.3","MACアドレス": "11:22:33:44:55:03"},
]


# ---------------------------------------------------------------------------
# 設定ファイル読み込み
# ---------------------------------------------------------------------------

@st.cache_resource
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)


# ---------------------------------------------------------------------------
# 認証セットアップ
# ---------------------------------------------------------------------------

def setup_authenticator(config: dict) -> stauth.Authenticate:
    return stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        cookie_key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
        auto_hash=True,    # config.yaml の平文パスワードを自動ハッシュ化
    )


def get_role(config: dict, username: str) -> str:
    return (
        config["credentials"]["usernames"]
        .get(username, {})
        .get("role", "viewer")
    )


def can(config: dict, role: str, permission: str) -> bool:
    return config["roles"].get(role, {}).get(permission, False)


# ---------------------------------------------------------------------------
# データ取得（短期キャッシュ 60秒）
# ★本番: DUMMY_ARP の代わりに get_arp_entries() を呼ぶ
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_arp_dataframe() -> tuple[pd.DataFrame, list[str]]:
    # ---（本番差し替え箇所 ここから）---
    rows = DUMMY_ARP.copy()
    errors: list[str] = []
    # ---（本番差し替え箇所 ここまで）---

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["スイッチ", "VLAN", "インターフェース", "IPアドレス", "MACアドレス"]
    )
    return df, errors


# ---------------------------------------------------------------------------
# ARPテーブル UI
# ---------------------------------------------------------------------------

def render_arp_page(config: dict, username: str):
    role = get_role(config, username)

    st.title("🔍 ARPテーブル リアルタイム確認")
    st.caption("コアスイッチからSNMPで取得（DB保存なし・キャッシュ60秒）　※現在はデモ用ダミーデータ表示")

    # 再取得ボタン（admin のみ）
    if can(config, role, "can_refresh"):
        if st.button("🔄 再取得"):
            st.cache_data.clear()
            st.rerun()

    # データ取得
    with st.spinner("ARPテーブルを取得中..."):
        df, errors = fetch_arp_dataframe()

    for msg in errors:
        st.warning(msg)

    if df.empty:
        st.error("ARPエントリを取得できませんでした。")
        return

    # フィルタ
    with st.expander("🔎 フィルタ", expanded=True):
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            sel_sw = st.multiselect(
                "スイッチ",
                options=sorted(df["スイッチ"].unique()),
            )
        with f2:
            sel_vlan = st.multiselect(
                "VLAN",
                options=sorted(df["VLAN"].dropna().astype(int).unique()),
            )
        with f3:
            ip_filter = st.text_input("IPアドレス（部分一致）", placeholder="10.0.10")
        with f4:
            mac_filter = st.text_input("MACアドレス（部分一致）", placeholder="aa:bb")

    # フィルタ適用
    filtered = df.copy()
    if sel_sw:
        filtered = filtered[filtered["スイッチ"].isin(sel_sw)]
    if sel_vlan:
        filtered = filtered[filtered["VLAN"].isin(sel_vlan)]
    if ip_filter:
        filtered = filtered[filtered["IPアドレス"].str.contains(ip_filter, na=False)]
    if mac_filter:
        filtered = filtered[filtered["MACアドレス"].str.contains(mac_filter, case=False, na=False)]

    # メトリクス
    m1, m2, m3 = st.columns(3)
    m1.metric("総エントリ数", len(df))
    m2.metric("フィルタ後", len(filtered))
    m3.metric("取得スイッチ数", df["スイッチ"].nunique())

    # テーブル
    st.dataframe(
        filtered.sort_values(["VLAN", "IPアドレス"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "VLAN": st.column_config.NumberColumn("VLAN", format="%d"),
        },
    )

    # CSV（admin のみ）
    if can(config, role, "can_download"):
        st.download_button(
            label="📥 CSV ダウンロード",
            data=filtered.to_csv(index=False).encode("utf-8-sig"),
            file_name="arp_table.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="ARPテーブル確認", layout="wide")

    config = load_config()
    authenticator = setup_authenticator(config)

    # ログインフォーム（新API: location のみ指定）
    result = authenticator.login(location="main")

    # 戻り値がNoneの場合（Cookie認証済みなど）はセッションから取得
    if result is not None:
        name, auth_status, username = result
    else:
        name        = st.session_state.get("name")
        auth_status = st.session_state.get("authentication_status")
        username    = st.session_state.get("username")

    if auth_status is True:
        with st.sidebar:
            role = get_role(config, username)
            st.markdown(f"**👤 {name}**")
            st.caption(f"ロール: `{role}`")
            st.divider()
            authenticator.logout(location="sidebar")

        render_arp_page(config, username)

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")

    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()
