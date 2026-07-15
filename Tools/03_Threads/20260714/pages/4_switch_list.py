"""
Streamlit ページ: スイッチ登録状況一覧
- YAML ベースのユーザー認証（既存ページと共通）
- DBに登録済みのスイッチ一覧を検索・ステータス確認
- 選択したスイッチのMACアドレステーブルをARP情報(IPアドレス)と突き合わせて表示
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
# データ取得：スイッチ一覧
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_switch_dataframe() -> pd.DataFrame:
    switches = Switch.fetch_all()
    if not switches:
        return pd.DataFrame(columns=[
            "ホスト名", "IPアドレス", "機種", "設置場所", "種類", "役割",
            "ステータス", "収集状況", "最終更新",
        ])

    df = pd.DataFrame(switches)
    df["ステータス"] = df["is_active"].map({True: "🟢 有効", False: "⚪ 無効"})
    df["収集状況"] = df["hardware_model"].apply(
        lambda m: "⚠️ 未収集" if m == "unknown" else "✅ 収集済み"
    )
    df["最終更新"] = df["updated_at"].apply(
        lambda v: v.strftime("%Y-%m-%d %H:%M") if pd.notna(v) else "-"
    )

    df = df.rename(columns={
        "hostname": "ホスト名",
        "ip_address": "IPアドレス",
        "hardware_model": "機種",
        "location": "設置場所",
        "switch_type": "種類",
        "role": "役割",
    })

    return df[["ホスト名", "IPアドレス", "機種", "設置場所", "種類", "役割",
               "ステータス", "収集状況", "最終更新"]]


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

def render_switch_list_page(config: dict, role: str):
    st.title("📋 スイッチ登録状況一覧")
    st.caption("DBに登録済みのスイッチと、収集状況を確認します")

    if st.button("🔄 表示を更新"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("データを取得中..."):
        df = fetch_switch_dataframe()

    if df.empty:
        st.warning("登録済みのスイッチがありません。CSV仮登録を実行してください。")
        return

    # ---- 集計メトリクス ----
    total = len(df)
    active_count = (df["ステータス"] == "🟢 有効").sum()
    uncollected_count = (df["収集状況"] == "⚠️ 未収集").sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("総登録数", total)
    m2.metric("有効", int(active_count))
    m3.metric("未収集(Inventory未実施)", int(uncollected_count))

    st.divider()

    # ---- 検索・フィルタUI ----
    with st.expander("🔎 検索・フィルタ", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)

        with f_col1:
            hostname_filter = st.text_input("ホスト名（部分一致）", placeholder="例: rx8")

        with f_col2:
            location_filter = st.text_input("設置場所（部分一致）", placeholder="例: UTM")

        with f_col3:
            ip_filter = st.text_input("IPアドレス（部分一致）", placeholder="例: 192.168.64")

        f_col4, f_col5, f_col6 = st.columns(3)

        with f_col4:
            role_options = sorted(df["役割"].dropna().unique().tolist())
            sel_roles = st.multiselect("役割", options=role_options)

        with f_col5:
            status_options = ["🟢 有効", "⚪ 無効"]
            sel_status = st.multiselect("ステータス", options=status_options)

        with f_col6:
            collect_options = ["✅ 収集済み", "⚠️ 未収集"]
            sel_collect = st.multiselect("収集状況", options=collect_options)

    # ---- フィルタ適用 ----
    filtered = df.copy()
    if hostname_filter:
        filtered = filtered[filtered["ホスト名"].str.contains(hostname_filter, case=False, na=False)]
    if location_filter:
        filtered = filtered[filtered["設置場所"].str.contains(location_filter, case=False, na=False)]
    if ip_filter:
        filtered = filtered[filtered["IPアドレス"].str.contains(ip_filter, na=False)]
    if sel_roles:
        filtered = filtered[filtered["役割"].isin(sel_roles)]
    if sel_status:
        filtered = filtered[filtered["ステータス"].isin(sel_status)]
    if sel_collect:
        filtered = filtered[filtered["収集状況"].isin(sel_collect)]

    st.caption(f"表示中: {len(filtered)}件 / 全{total}件")

    # ---- テーブル表示 ----
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    # ---- CSVエクスポート（admin のみ）----
    if can(config, role, "can_download"):
        st.download_button(
            label="📥 CSV ダウンロード",
            data=filtered.to_csv(index=False).encode("utf-8-sig"),
            file_name="switch_list.csv",
            mime="text/csv",
            key="switch_list_download",
        )

    # ---- MACアドレステーブル表示 ----
    st.divider()
    st.subheader("🔌 MACアドレステーブル")
    st.caption("選択したスイッチのMACアドレステーブルを、ARP情報からIPアドレスと突き合わせて表示します")

    hostname_options = sorted(df["ホスト名"].tolist())
    selected_hostname = st.selectbox("スイッチを選択", options=["(選択してください)"] + hostname_options)

    if selected_hostname != "(選択してください)":
        switch_full = Switch.fetch_by_hostname(selected_hostname)

        if switch_full is None:
            st.warning("スイッチ情報の取得に失敗しました。")
        else:
            with st.spinner("MACアドレステーブルを取得中..."):
                mac_df = fetch_mac_table_with_ip(switch_full["id"])

            if mac_df.empty:
                st.info(f"`{selected_hostname}` のMACアドレステーブルはまだ収集されていません。")
            else:
                mm1, mm2 = st.columns(2)
                mm1.metric("登録エントリ数", len(mac_df))
                mm2.metric("IP不明のエントリ", int((mac_df["IPアドレス"] == "不明").sum()))

                st.dataframe(mac_df, use_container_width=True, hide_index=True)

                if can(config, role, "can_download"):
                    st.download_button(
                        label="📥 CSV ダウンロード",
                        data=mac_df.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"mac_table_{selected_hostname}.csv",
                        mime="text/csv",
                        key="mac_table_download",
                    )


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="スイッチ登録状況", layout="wide")

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

        render_switch_list_page(config, role)

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()