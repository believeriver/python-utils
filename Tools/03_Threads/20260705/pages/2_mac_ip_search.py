"""
Streamlit ページ: MAC / IPアドレス検索
- YAML ベースのユーザー認証（streamlit-authenticator、既存と共通）
- DBはSQLite（収集済みデータを検索するのみ、外部通信なし）
"""

from __future__ import annotations
import sys
import re
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.mac_address import MacAddressEntry, MacAddressHistory
from models.arp_entry import ArpEntry
from models.switch import Switch
from models.db import database

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


# ---------------------------------------------------------------------------
# 設定・認証（arp_table.pyと共通のパターン）
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
# 検索ロジック
# ---------------------------------------------------------------------------

def normalize_mac(raw: str) -> str:
    hex_only = re.sub(r"[^0-9a-fA-F]", "", raw).lower()
    if len(hex_only) != 12:
        return ""
    return ":".join(hex_only[i:i + 2] for i in range(0, 12, 2))


def is_ip_format(raw: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", raw.strip()))


def resolve_mac_from_query(query: str) -> str | None:
    query = query.strip()
    if is_ip_format(query):
        arp = ArpEntry.fetch_by_ip(query)
        return arp["mac_address"] if arp else None
    mac = normalize_mac(query)
    return mac if mac else None


def search_mac_full_history(mac_address: str) -> dict:
    current = MacAddressEntry.fetch_by_mac(mac_address)
    history = MacAddressHistory.fetch_by_mac(mac_address)
    arp_list = ArpEntry.fetch_by_mac(mac_address)

    timeline = list(history)
    if current:
        timeline.append({
            "switch_hostname": current["switch_hostname"],
            "port": current["port"],
            "vlan": current["vlan"],
            "valid_from": current["first_seen"],
            "valid_to": None,
        })

    return {"mac_address": mac_address, "current": current, "timeline": timeline, "arp_entries": arp_list}


# ---------------------------------------------------------------------------
# ページ本体 UI
# ---------------------------------------------------------------------------

def render_search_page(config: dict, username: str):
    role = get_role(config, username)

    st.title("🔍 MAC / IPアドレス検索")
    st.caption("収集済みデータから、機器の接続先スイッチ・接続履歴を検索します（DB参照・都度通信なし）")

    query = st.text_input(
        "MACアドレスまたはIPアドレスを入力してください",
        placeholder="例: aa:bb:cc:dd:ee:01 または 192.168.64.2",
    )

    if not query:
        return

    mac_address = resolve_mac_from_query(query)
    st.write(f"DEBUG: resolved mac_address = `{mac_address}`")
    if mac_address is None:
        st.warning("該当する端末が見つかりませんでした。入力形式をご確認ください。")
        return

    result = search_mac_full_history(mac_address)
    current = result["current"]
    timeline = result["timeline"]

    if current is None and not timeline:
        st.warning(f"MACアドレス `{mac_address}` の記録が見つかりませんでした。")
        return

    st.subheader("現在の接続状況")
    if current:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("接続スイッチ", current["switch_hostname"])
        c2.metric("ポート", current["port"])
        c3.metric("VLAN", current["vlan"])
        c4.metric("最終確認", current["last_seen"].strftime("%Y-%m-%d %H:%M"))
    else:
        # st.info("現在このMACアドレスは、どのスイッチにも接続が確認されていません（過去の履歴のみ存在）。")
        session = database.connect_db()
        is_switch_itself = session.query(Switch).filter(
            Switch.base_mac_address == mac_address
        ).first()
        switch_hostname = is_switch_itself.hostname if is_switch_itself else None
        session.close()

        if switch_hostname:
            st.info(f"このMACアドレスは、スイッチ `{switch_hostname}` 自身のものです。")
        else:
            st.info("現在このMACアドレスは、どのスイッチにも接続が確認されていません（過去の履歴のみ存在）。")

    ip_list = sorted({e["ip_address"] for e in result["arp_entries"]})
    st.caption(f"MACアドレス: `{mac_address}` ／ 関連IPアドレス: {', '.join(ip_list) if ip_list else '不明'}")

    st.divider()
    st.subheader("接続履歴（タイムライン）")

    if not timeline:
        st.info("履歴データはありません。")
        return

    df = pd.DataFrame(timeline).sort_values("valid_from", ascending=False)
    # df["接続終了"] = df["valid_to"].apply(lambda v: v.strftime("%Y-%m-%d %H:%M") if v is not None else "現在")
    # df["接続開始"] = df["valid_from"].apply(lambda v: v.strftime("%Y-%m-%d %H:%M"))
    df["接続終了"] = df["valid_to"].apply(
        lambda v: "現在" if pd.isna(v) else v.strftime("%Y-%m-%d %H:%M")
    )
    df["接続開始"] = df["valid_from"].apply(
        lambda v: "現在" if pd.isna(v) else v.strftime("%Y-%m-%d %H:%M")
    )
    df = df.rename(columns={"switch_hostname": "スイッチ", "port": "ポート", "vlan": "VLAN"})

    st.dataframe(
        df[["スイッチ", "ポート", "VLAN", "接続開始", "接続終了"]],
        use_container_width=True,
        hide_index=True,
        column_config={"VLAN": st.column_config.NumberColumn("VLAN", format="%d")},
    )

    if can(config, role, "can_download"):
        st.download_button(
            label="📥 CSV ダウンロード",
            data=df[["スイッチ", "ポート", "VLAN", "接続開始", "接続終了"]].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"mac_history_{mac_address.replace(':', '')}.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# エントリーポイント（arp_table.pyと共通のログインフロー）
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="MAC/IP検索", layout="wide")

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
        with st.sidebar:
            role = get_role(config, username)
            st.markdown(f"**👤 {name}**")
            st.caption(f"ロール: `{role}`")
            st.divider()
            authenticator.logout("ログアウト", location="sidebar")

        render_search_page(config, username)

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()