"""
Streamlit ページ: ARPテーブル リアルタイム確認
- YAML ベースのユーザー認証（streamlit-authenticator）
- ロール別機能制御（admin / viewer）
- DB保存なし / st.cache_data(ttl=60) で短期キャッシュ
"""

from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

# snmp モジュールをパスに追加（プロジェクト構成に合わせて調整）
sys.path.append(str(Path(__file__).resolve().parents[1]))
from snmp.arp_collector import get_arp_entries


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

CORE_SWITCHES = [
    {"host": "192.168.0.1", "community": "public", "label": "Core-SW1"},
    {"host": "192.168.0.2", "community": "public", "label": "Core-SW2"},
]


# ---------------------------------------------------------------------------
# 設定ファイル読み込み
# ---------------------------------------------------------------------------

@st.cache_resource
def load_config() -> dict:
    """config.yaml を読み込む（アプリ起動時1回のみ）"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)


# ---------------------------------------------------------------------------
# 認証
# ---------------------------------------------------------------------------

def setup_authenticator(config: dict) -> stauth.Authenticate:
    return stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        cookie_key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
    )


def get_role(config: dict, username: str) -> str:
    """ユーザー名からロールを取得。未設定の場合は viewer を返す"""
    return (
        config["credentials"]["usernames"]
        .get(username, {})
        .get("role", "viewer")
    )


def can(config: dict, role: str, permission: str) -> bool:
    """ロール権限チェック"""
    return config["roles"].get(role, {}).get(permission, False)


# ---------------------------------------------------------------------------
# データ取得（短期キャッシュ: 60秒）
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_arp_dataframe() -> tuple[pd.DataFrame, list[str]]:
    """
    全コアスイッチからARPエントリを取得してDataFrameに変換。
    errors: 取得失敗スイッチのメッセージリスト。
    """
    rows: list[dict] = []
    errors: list[str] = []

    for sw in CORE_SWITCHES:
        try:
            entries = get_arp_entries(
                host=sw["host"],
                community=sw["community"],
                label=sw["label"],
            )
            for e in entries:
                rows.append({
                    "スイッチ":         e.switch_label,
                    "VLAN":             e.vlan_id,
                    "インターフェース": e.interface,
                    "IPアドレス":       e.ip_address,
                    "MACアドレス":      e.mac_address,
                })
        except Exception as ex:
            errors.append(f"⚠️ {sw['label']} ({sw['host']}): {ex}")

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["スイッチ", "VLAN", "インターフェース", "IPアドレス", "MACアドレス"]
    )
    return df, errors


# ---------------------------------------------------------------------------
# ARPテーブル本体 UI
# ---------------------------------------------------------------------------

def render_arp_page(config: dict, username: str, display_name: str):
    role = get_role(config, username)

    st.title("🔍 ARPテーブル リアルタイム確認")
    st.caption("コアスイッチからSNMPで取得（DB保存なし・キャッシュ60秒）")

    # ---- 再取得ボタン（admin のみ表示）----
    if can(config, role, "can_refresh"):
        if st.button("🔄 再取得", use_container_width=False):
            st.cache_data.clear()
            st.rerun()

    # ---- データ取得 ----
    with st.spinner("SNMPでARPテーブルを取得中..."):
        df, errors = fetch_arp_dataframe()

    # ---- エラー表示 ----
    for msg in errors:
        st.warning(msg)

    if df.empty:
        st.error("ARPエントリを取得できませんでした。")
        return

    # ---- フィルタUI ----
    with st.expander("🔎 フィルタ", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            sw_labels = sorted(df["スイッチ"].unique().tolist())
            sel_sw = st.multiselect("スイッチ", options=sw_labels)

        with f_col2:
            vlans = sorted(df["VLAN"].dropna().astype(int).unique().tolist())
            sel_vlan = st.multiselect("VLAN", options=vlans)

        with f_col3:
            ip_filter = st.text_input("IPアドレス（部分一致）", placeholder="192.168.10")

        with f_col4:
            mac_filter = st.text_input("MACアドレス（部分一致）", placeholder="aa:bb")

    # ---- フィルタ適用 ----
    filtered = df.copy()
    if sel_sw:
        filtered = filtered[filtered["スイッチ"].isin(sel_sw)]
    if sel_vlan:
        filtered = filtered[filtered["VLAN"].isin(sel_vlan)]
    if ip_filter:
        filtered = filtered[filtered["IPアドレス"].str.contains(ip_filter, na=False)]
    if mac_filter:
        filtered = filtered[
            filtered["MACアドレス"].str.contains(mac_filter, case=False, na=False)
        ]

    # ---- 集計メトリクス ----
    m1, m2, m3 = st.columns(3)
    m1.metric("総エントリ数", len(df))
    m2.metric("フィルタ後", len(filtered))
    m3.metric("取得スイッチ数", df["スイッチ"].nunique())

    # ---- テーブル表示 ----
    st.dataframe(
        filtered.sort_values(["VLAN", "IPアドレス"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "VLAN": st.column_config.NumberColumn("VLAN", format="%d"),
        },
    )

    # ---- CSVエクスポート（admin のみ表示）----
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

    # ---- ログインフォーム ----
    # name, auth_status, username = authenticator.login(
    #     form_name="ログイン",
    #     location="main",
    # )
    result = authenticator.login(location="main")

    if result is not None:
        name, auth_status, username = result
    else:
        name = st.session_state.get("name")
        auth_status = st.session_state.get("authentication_status")
        username = st.session_state.get("username")

    # ---- 認証結果ハンドリング ----
    if auth_status is True:
        # サイドバー: ユーザー情報 + ログアウト
        with st.sidebar:
            role = get_role(config, username)
            st.markdown(f"**👤 {name}**")
            st.caption(f"ロール: `{role}`")
            st.divider()
            authenticator.logout("ログアウト", location="sidebar")

        render_arp_page(config, username, name)

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")

    else:  # None: 未入力
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()
