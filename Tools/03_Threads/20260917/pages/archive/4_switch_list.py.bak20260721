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
from models.liveness import Liveness

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
            "ステータス", "収集状況", "Ping", "SSH", "死活確認", "最終更新",
        ])

    liveness_list = Liveness.fetch_all()
    liveness_map = {l["switch_id"]: l for l in liveness_list}

    df = pd.DataFrame(switches)
    df["ステータス"] = df["is_active"].map({True: "🟢 有効", False: "⚪ 無効"})
    df["情報取得"] = df["hardware_model"].apply(
        lambda m: "⚠️ 未取得" if m == "unknown" else "✅ 取得済み"
    )
    df["最終更新"] = df["updated_at"].apply(
        lambda v: v.strftime("%Y-%m-%d %H:%M") if pd.notna(v) else "-"
    )

    def _ping_status(sid):
        if sid not in liveness_map:
            return "⚪ 未確認"
        return "🟢 応答あり" if liveness_map[sid]["ping_ok"] else "🔴 応答なし"

    def _ssh_status(sid):
        if sid not in liveness_map:
            return "⚪ 未確認"
        return "🟢 成功" if liveness_map[sid]["ssh_ok"] else "🔴 失敗"

    def _checked_at(sid):
        if sid not in liveness_map or liveness_map[sid]["checked_at"] is None:
            return "-"
        return liveness_map[sid]["checked_at"].strftime("%Y-%m-%d %H:%M")

    df["Ping"] = df["id"].apply(_ping_status)
    df["SSH"] = df["id"].apply(_ssh_status)
    df["死活確認"] = df["id"].apply(_checked_at)

    df = df.rename(columns={
        "hostname": "ホスト名", "ip_address": "IPアドレス", "hardware_model": "機種",
        "location": "設置場所", "switch_type": "種類", "role": "役割",
    })

    return df[["ホスト名", "IPアドレス", "機種", "設置場所", "種類", "役割",
               "ステータス", "情報取得", "Ping", "SSH", "死活確認", "最終更新"]]


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
    uncollected_count = (df["情報取得"] == "⚠️ 未取得").sum()
    ping_fail_count = (df["Ping"] == "🔴 応答なし").sum()
    ssh_fail_count = (df["SSH"] == "🔴 失敗").sum()

    m1, m2, m3 = st.columns(3)

    m1.metric("総登録数", total)
    m2.metric("有効", int(active_count))
    m3.metric("未取得(Inventory未実施)", int(uncollected_count))

    m4, m5 = st.columns(2)
    m4.metric("Ping失敗", int(ping_fail_count))
    m5.metric("SSH失敗", int(ssh_fail_count))

    # ---- サービスタグ重複チェック ----
    # duplicates = Switch.find_duplicate_service_tags()
    # if duplicates:
    #     with st.expander(f"⚠️ サービスタグ重複: {len(duplicates)}件（有効なスイッチ間）", expanded=True):
    #         for d in duplicates:
    #             st.warning(f"サービスタグ `{d['service_tag']}` が複数の有効なスイッチに登録されています: {', '.join(d['hostnames'])}")
    #
    # st.divider()
    duplicate_ips = Switch.find_duplicate_ip_addresses()
    duplicate_tags = Switch.find_duplicate_service_tags()

    if duplicate_ips or duplicate_tags:
        with st.expander(
                f"⚠️ 重複あり: IPアドレス{len(duplicate_ips)}件 / サービスタグ{len(duplicate_tags)}件（有効なスイッチ間）",
                expanded=True,
        ):
            for d in duplicate_ips:
                st.warning(
                    f"IPアドレス `{d['ip_address']}` が複数の有効なスイッチに登録されています: {', '.join(d['hostnames'])}")
            for d in duplicate_tags:
                st.warning(
                    f"サービスタグ `{d['service_tag']}` が複数の有効なスイッチに登録されています: {', '.join(d['hostnames'])}")

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

        f_col4, f_col5, f_col6, f_col7, f_col8 = st.columns(5)

        with f_col4:
            role_options = sorted(df["役割"].dropna().unique().tolist())
            sel_roles = st.multiselect("役割", options=role_options)

        with f_col5:
            status_options = ["🟢 有効", "⚪ 無効"]
            sel_status = st.multiselect("ステータス", options=status_options, default=["🟢 有効"])

        with f_col6:
            collect_options = ["✅ 取得済み", "⚠️ 未取得"]
            sel_collect = st.multiselect("情報取得", options=collect_options)

        with f_col7:
            ping_options = ["🟢 応答あり", "🔴 応答なし", "⚪ 未確認"]
            sel_ping = st.multiselect("Ping", options=ping_options)

        with f_col8:
            ssh_options = ["🟢 成功", "🔴 失敗", "⚪ 未確認"]
            sel_ssh = st.multiselect("SSH", options=ssh_options)

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
        filtered = filtered[filtered["情報取得"].isin(sel_collect)]
    if sel_ping:
        filtered = filtered[filtered["Ping"].isin(sel_ping)]
    if sel_ssh:
        filtered = filtered[filtered["SSH"].isin(sel_ssh)]

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