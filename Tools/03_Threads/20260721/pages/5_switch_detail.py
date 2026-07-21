"""
Streamlit ページ: スイッチ詳細（ポート・MACアドレステーブル）
- YAML ベースのユーザー認証（既存ページと共通）
- ホスト名/IPアドレス/設置場所で検索 → 1台選択 → MACアドレステーブルをARPで
  IP紐付けして表示
"""

from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.switch import Switch
from models.mac_address import MacAddressEntry
from models.arp_entry import ArpEntry

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


# ---------------------------------------------------------------------------
# 設定・認証（既存ページと共通のパターン）
# ---------------------------------------------------------------------------

@st.cache_resource
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)


def setup_authenticator(config: dict) -> stauth.Authenticate:
    return stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        cookie_key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
    )


def get_role(config: dict, username: str) -> str:
    return config["credentials"]["usernames"].get(username, {}).get("role", "viewer")


def can(config: dict, role: str, permission: str) -> bool:
    return config["roles"].get(role, {}).get(permission, False)


# ---------------------------------------------------------------------------
# データ取得：スイッチ検索用の一覧（軽量フィールドのみ）
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_switch_dataframe() -> pd.DataFrame:
    switches = Switch.fetch_all()
    if not switches:
        return pd.DataFrame(columns=["ホスト名", "IPアドレス", "設置場所", "役割", "ステータス"])

    df = pd.DataFrame(switches)
    df["ステータス"] = df["is_active"].map({True: "🟢 有効", False: "⚪ 無効"})
    df = df.rename(columns={
        "hostname": "ホスト名",
        "ip_address": "IPアドレス",
        "location": "設置場所",
        "role": "役割",
    })
    return df[["ホスト名", "IPアドレス", "設置場所", "役割", "ステータス"]]


# ---------------------------------------------------------------------------
# データ取得：MACアドレステーブル（ARPでIP紐付け）
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_mac_table_with_ip(switch_id: int) -> pd.DataFrame:
    """指定スイッチのMACアドレステーブルに、ARP情報からIPアドレスを紐付けて返す"""
    entries = MacAddressEntry.fetch_by_switch(switch_id)
    if not entries:
        return pd.DataFrame(columns=["VLAN", "MACアドレス", "ポート", "IPアドレス", "最終確認"])

    mac_list = [e["mac_address"] for e in entries]
    mac_to_ip = ArpEntry.fetch_mac_to_ip_map(mac_list)

    rows = []
    for e in entries:
        ip_list = mac_to_ip.get(e["mac_address"], [])
        rows.append({
            "VLAN": e["vlan"],
            "MACアドレス": e["mac_address"],
            "ポート": e["port"],
            "IPアドレス": ", ".join(ip_list) if ip_list else "不明",
            "最終確認": e["last_seen"].strftime("%Y-%m-%d %H:%M") if e["last_seen"] else "-",
        })

    return pd.DataFrame(rows).sort_values(["VLAN", "ポート"])


# ---------------------------------------------------------------------------
# ページ本体 UI
# ---------------------------------------------------------------------------

def render_switch_detail_page(config: dict, role: str):
    st.title("🔎 スイッチ詳細")
    st.caption("スイッチを検索して、ポート状況・MACアドレステーブルを確認します")

    df = fetch_switch_dataframe()

    if df.empty:
        st.warning("登録済みのスイッチがありません。")
        return

    # ---- 検索(部分一致、500台規模を想定しドロップダウンは使わない) ----
    query = st.text_input(
        "ホスト名・IPアドレス・設置場所で検索",
        placeholder="例: rx8headnode / 192.168.64 / UTM",
    )

    if not query:
        st.info("検索キーワードを入力してください。")
        return

    matched = df[
        df["ホスト名"].str.contains(query, case=False, na=False)
        | df["IPアドレス"].str.contains(query, case=False, na=False)
        | df["設置場所"].str.contains(query, case=False, na=False)
    ]

    if matched.empty:
        st.warning(f"`{query}` に該当するスイッチが見つかりませんでした。")
        return

    if len(matched) > 1:
        st.caption(f"{len(matched)}件ヒットしました。対象を選択してください。")
        selected_hostname = st.selectbox("対象スイッチ", options=matched["ホスト名"].tolist())
    else:
        selected_hostname = matched["ホスト名"].iloc[0]

    switch_row = matched[matched["ホスト名"] == selected_hostname].iloc[0]

    st.divider()

    # ---- 基本情報 ----
    st.subheader(f"📟 {selected_hostname}")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("IPアドレス", switch_row["IPアドレス"])
    b2.metric("設置場所", switch_row["設置場所"] or "-")
    b3.metric("役割", switch_row["役割"])
    b4.metric("ステータス", switch_row["ステータス"])

    st.divider()

    # ---- MACアドレステーブル ----
    st.subheader("🔌 MACアドレステーブル")

    switch_full = Switch.fetch_by_hostname(selected_hostname)
    if switch_full is None:
        st.warning("スイッチ情報の取得に失敗しました。")
        return

    with st.spinner("MACアドレステーブルを取得中..."):
        mac_df = fetch_mac_table_with_ip(switch_full["id"])

    if mac_df.empty:
        st.info(f"`{selected_hostname}` のMACアドレステーブルはまだ収集されていません。")
        return

    mm1, mm2 = st.columns(2)
    mm1.metric("登録エントリ数", len(mac_df))
    mm2.metric("IP不明のエントリ", int((mac_df["IPアドレス"] == "不明").sum()))

    # ---- ポート/VLANでの絞り込み ----
    with st.expander("🔎 絞り込み", expanded=False):
        fc1, fc2 = st.columns(2)
        with fc1:
            vlan_options = sorted(mac_df["VLAN"].dropna().unique().tolist())
            sel_vlans = st.multiselect("VLAN", options=vlan_options)
        with fc2:
            port_filter = st.text_input("ポート（部分一致）", placeholder="例: Gi1/0")

    filtered_mac_df = mac_df.copy()
    if sel_vlans:
        filtered_mac_df = filtered_mac_df[filtered_mac_df["VLAN"].isin(sel_vlans)]
    if port_filter:
        filtered_mac_df = filtered_mac_df[
            filtered_mac_df["ポート"].str.contains(port_filter, case=False, na=False)
        ]

    st.caption(f"表示中: {len(filtered_mac_df)}件 / 全{len(mac_df)}件")
    st.dataframe(filtered_mac_df, use_container_width=True, hide_index=True)

    if can(config, role, "can_download"):
        st.download_button(
            label="📥 CSV ダウンロード",
            data=filtered_mac_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"mac_table_{selected_hostname}.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="スイッチ詳細", layout="wide")

    config = load_config()
    authenticator = setup_authenticator(config)

    result = authenticator.login(location="main")
    if result is not None:
        name, auth_status, username = result
    else:
        name = st.session_state.get("name")
        auth_status = st.session_state.get("authentication_status")
        username = st.session_state.get("username")

    if auth_status is True:
        role = get_role(config, username)

        with st.sidebar:
            st.markdown(f"**👤 {name}**")
            st.caption(f"ロール: `{role}`")
            st.divider()
            authenticator.logout("ログアウト", location="sidebar")

        render_switch_detail_page(config, role)

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()