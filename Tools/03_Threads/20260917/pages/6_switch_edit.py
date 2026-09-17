"""
Streamlit ページ: スイッチ登録・編集
- admin のみアクセス可能
- 既存スイッチの編集 / 新規スイッチの手動追加
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

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

SWITCH_TYPE_OPTIONS = ["L2", "L3"]
ROLE_OPTIONS = ["core", "floor", "edge"]


# ---------------------------------------------------------------------------
# 設定・認証
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
# データ取得
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def fetch_hostname_list() -> list:
    switches = Switch.fetch_all()
    return sorted([s["hostname"] for s in switches])


# ---------------------------------------------------------------------------
# 編集フォーム
# ---------------------------------------------------------------------------

def render_edit_form():
    st.subheader("✏️ 既存スイッチの編集")

    hostnames = fetch_hostname_list()
    if not hostnames:
        st.info("登録済みのスイッチがありません。")
        return

    query = st.text_input("編集するホスト名を検索", placeholder="例: rx8headnode")
    candidates = [h for h in hostnames if query.lower() in h.lower()] if query else []

    if not query:
        return
    if not candidates:
        st.warning("該当するホストが見つかりませんでした。")
        return

    selected = st.selectbox("編集対象", options=candidates) if len(candidates) > 1 else candidates[0]
    current = Switch.fetch_by_hostname(selected)

    if current is None:
        st.error("データの取得に失敗しました。")
        return

    with st.form(f"edit_form_{selected}"):
        st.caption(f"編集中: **{selected}**")

        ip_address = st.text_input("IPアドレス", value=current["ip_address"])
        location = st.text_input("設置場所", value=current["location"] or "")
        switch_type = st.selectbox(
            "種類(L2/L3)", options=SWITCH_TYPE_OPTIONS,
            index=SWITCH_TYPE_OPTIONS.index(current.get("switch_type", "L2"))
            if current.get("switch_type") in SWITCH_TYPE_OPTIONS else 0,
        )
        role = st.selectbox(
            "役割", options=ROLE_OPTIONS,
            index=ROLE_OPTIONS.index(current.get("role", "edge"))
            if current.get("role") in ROLE_OPTIONS else 2,
        )
        is_active = st.checkbox("有効", value=current.get("is_active", True))

        submitted = st.form_submit_button("💾 保存")

        if submitted:
            if not ip_address.strip():
                st.error("IPアドレスは必須です。")
            else:
                Switch.get_or_create(
                    hostname=selected,
                    ip_address=ip_address.strip(),
                    hardware_model=current.get("hardware_model") or "unknown",
                    switch_type=switch_type,
                    role=role,
                    location=location.strip() or None,
                    is_active=is_active,
                )
                st.success(f"`{selected}` を更新しました。")
                st.cache_data.clear()
                st.rerun()


# ---------------------------------------------------------------------------
# 新規追加フォーム
# ---------------------------------------------------------------------------

def render_create_form():
    st.subheader("➕ スイッチの新規追加")
    st.caption("CSV反映前の緊急追加や、単発の追加登録に利用してください")

    with st.form("create_form"):
        hostname = st.text_input("ホスト名 *")
        ip_address = st.text_input("IPアドレス *")
        location = st.text_input("設置場所")
        switch_type = st.selectbox("種類(L2/L3) *", options=SWITCH_TYPE_OPTIONS)
        role = st.selectbox("役割 *", options=ROLE_OPTIONS)

        submitted = st.form_submit_button("➕ 追加")

        if submitted:
            hostnames = fetch_hostname_list()
            if not hostname.strip() or not ip_address.strip():
                st.error("ホスト名とIPアドレスは必須です。")
            elif hostname.strip() in hostnames:
                st.error(f"`{hostname}` はすでに登録されています。編集タブから更新してください。")
            else:
                Switch.get_or_create(
                    hostname=hostname.strip(),
                    ip_address=ip_address.strip(),
                    hardware_model="unknown",
                    switch_type=switch_type,
                    role=role,
                    location=location.strip() or None,
                )
                st.success(f"`{hostname}` を新規追加しました。")
                st.cache_data.clear()
                st.rerun()

# ----------------------------------------------------------------------------
# 2026.08.20
# 無効化リスト
# ----------------------------------------------------------------------------
# pages/6_switch_edit.py に追加

def render_bulk_activate_form():
    st.subheader("♻️ 無効化スイッチの一括有効化")
    st.caption("誤って無効化した場合や、再稼働させる機器をまとめて有効化します")

    inactive = Switch.fetch_inactive()

    if not inactive:
        st.info("無効化されているスイッチはありません。")
        return

    df = pd.DataFrame(inactive)
    df = df.rename(columns={
        "hostname": "ホスト名", "ip_address": "IPアドレス",
        "hardware_model": "機種", "location": "設置場所", "role": "役割",
    })
    df["選択"] = False

    st.caption(f"無効化されているスイッチ: {len(df)}件")

    edited = st.data_editor(
        df[["選択", "ホスト名", "IPアドレス", "機種", "設置場所", "役割"]],
        use_container_width=True,
        hide_index=True,
        disabled=["ホスト名", "IPアドレス", "機種", "設置場所", "役割"],  # 選択列以外は編集不可
        key="bulk_activate_editor",
    )

    selected = edited[edited["選択"] == True]["ホスト名"].tolist()

    if selected:
        st.info(f"{len(selected)}件を有効化します: {', '.join(selected[:5])}{' ...' if len(selected) > 5 else ''}")

        if st.button("♻️ 選択したスイッチを有効化", type="primary"):
            success = []
            failed = []
            for hostname in selected:
                if Switch.activate(hostname):
                    success.append(hostname)
                else:
                    failed.append(hostname)

            st.success(f"{len(success)}件を有効化しました。")
            if failed:
                st.error(f"{len(failed)}件で失敗しました: {', '.join(failed)}")

            st.cache_data.clear()
            st.rerun()
    else:
        st.caption("有効化したいスイッチの「選択」列にチェックを入れてください。")

# ---------------------------------------------------------------------------
# ページ本体
# ---------------------------------------------------------------------------

def render_switch_edit_page():
    st.title("🛠️ スイッチ登録・編集")

    tab1, tab2, tab3 = st.tabs(["✏️ 編集", "➕ 新規追加", "♻️ 一括有効化"])
    with tab1:
        render_edit_form()
    with tab2:
        render_create_form()
    with tab3:
        render_bulk_activate_form()


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="スイッチ登録・編集", layout="wide")

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

        if can(config, role, "can_edit_switch"):  # admin権限の判定に既存キーを流用
            render_switch_edit_page()
        else:
            st.error("🔒 このページを閲覧する権限がありません（管理者のみ利用可能です）")

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()