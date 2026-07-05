"""
Streamlit ページ: ネットワークトポロジー可視化
- CDPネイバー情報(DB)を元にスイッチ間の接続関係をグラフ表示
- YAML ベースのユーザー認証（既存ページと共通）
"""

from __future__ import annotations
import sys
from pathlib import Path
import re

import streamlit as st
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from streamlit_agraph import agraph, Node, Edge, Config

sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.cdp_neighbor import CdpNeighbor
from models.switch import Switch
from models.db import database

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

ROLE_COLORS = {
    "core": "#e74c3c",     # 赤
    "floor": "#2ecc71",    # 緑
    "edge": "#3498db",     # 青
}
ROLE_SIZES = {
    "core": 28,
    "floor": 20,
    "edge": 14,
}
UNKNOWN_COLOR = "#95a5a6"  # グレー(未解決の機器)
UNKNOWN_SIZE = 10


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


# ---------------------------------------------------------------------------
# データ取得(DB参照のみ、SNMP/SSH通信なし)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def fetch_topology_data():
    nodes = CdpNeighbor.fetch_topology_nodes()
    edges = CdpNeighbor.fetch_topology_edges()
    return nodes, edges


@st.cache_data(ttl=300, show_spinner=False)
def fetch_switch_roles() -> dict:
    """hostname -> role の対応表(色分け用)"""
    session = database.connect_db()
    rows = session.query(Switch).all()
    result = {row.hostname: row.role for row in rows}
    session.close()
    return result


# ---------------------------------------------------------------------------
# グラフ構築
# ---------------------------------------------------------------------------

def is_ip_format(raw: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", raw.strip()))


def resolve_center_hostname(query: str) -> str | None:
    """入力(ホスト名またはIP)から、起点となるホスト名を解決する"""
    query = query.strip()
    if not query:
        return None

    if is_ip_format(query):
        switch = Switch.fetch_by_ip(query)
        return switch["hostname"] if switch else None

    switch = Switch.fetch_by_hostname(query)
    return switch["hostname"] if switch else None


def build_graph_elements(nodes: list, edges: list, role_map: dict, show_labels: bool = False):
    agraph_nodes = []
    for n in nodes:
        hostname = n["hostname"]
        ip_address = n.get("ip_address")

        if n["resolved"]:
            role = role_map.get(hostname, "edge")
            color = ROLE_COLORS.get(role, ROLE_COLORS["edge"])
            size = ROLE_SIZES.get(role, ROLE_SIZES["edge"])
        else:
            color = UNKNOWN_COLOR
            size = UNKNOWN_SIZE

        label = f"{hostname}\n{ip_address}" if ip_address else hostname

        agraph_nodes.append(Node(id=hostname, label=label, size=size, color=color))

    agraph_edges = []
    for e in edges:
        label = f'{e["port_a"]} - {e["port_b"] or "?"}' if show_labels else ""
        agraph_edges.append(Edge(
            source=e["switch_a"],
            target=e["switch_b"],
            label=label,
            dashes=not e["confirmed_both_sides"],
            color="#7f8c8d" if e["confirmed_both_sides"] else "#e67e22",
        ))

    return agraph_nodes, agraph_edges

# ---------------------------------------------------------------------------
# ページ本体 UI
# ---------------------------------------------------------------------------

def render_topology_page():
    st.title("🗺️ ネットワークトポロジー")
    st.caption("収集済みCDPネイバー情報を元にした接続構成図（DB参照・都度通信なし）")

    # ---- 起点・ホップ数の指定 ----
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input(
            "起点のホスト名またはIPアドレス（空欄なら全体表示）",
            placeholder="例: rx8headnode または 192.168.64.2",
        )
    with col2:
        max_hops = st.slider("表示するホップ数", min_value=1, max_value=5, value=2)
    with col3:
        show_labels = st.checkbox("ポート名を表示", value=False)

    if st.button("🔄 表示を更新"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("トポロジーデータを取得中..."):
        if not query:
            nodes, edges = fetch_topology_data()
            center = None
        else:
            center = resolve_center_hostname(query)
            if center is None:
                st.warning(f"`{query}` に該当するスイッチが見つかりませんでした。")
                return
            subgraph = CdpNeighbor.fetch_topology_subgraph(center, max_hops=max_hops)
            nodes, edges = subgraph["nodes"], subgraph["edges"]

        role_map = fetch_switch_roles()

    if not nodes:
        st.warning("該当するトポロジーデータがありません。")
        return

    if center:
        st.caption(f"起点: **{center}**（入力: {query}） / ホップ数: {max_hops}")

    # ---- 集計メトリクス ----
    m1, m2, m3 = st.columns(3)
    m1.metric("表示中のノード数", len(nodes))
    m2.metric("表示中のリンク数", len(edges))
    unresolved_count = sum(1 for n in nodes if not n["resolved"])
    m3.metric("未識別の機器", unresolved_count)

    # ---- 片側のみ確認のリンク一覧 ----
    unconfirmed_edges = [e for e in edges if not e["confirmed_both_sides"]]
    if unconfirmed_edges:
        with st.expander(f"⚠️ 片側からしか確認できていないリンク（{len(unconfirmed_edges)}件）", expanded=False):
            for e in unconfirmed_edges:
                st.write(f"- {e['switch_a']} ({e['port_a']}) → {e['switch_b']} ({e['port_b'] or '不明'})")

    st.divider()

    # ---- グラフ描画 ----
    agraph_nodes, agraph_edges = build_graph_elements(nodes, edges, role_map, show_labels)

    config = Config(
        width=1000,
        height=650,
        directed=False,
        physics=True,
        hierarchical=False,
        collapsible=False,
    )

    agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

    st.divider()
    st.caption(
        "🔴 コアスイッチ　🟢 フロアスイッチ　🔵 エッジスイッチ　⚪ 未識別の機器（IP電話・AP等）　"
        "点線 = 片側からのみ確認されたリンク"
    )

def can(config: dict, role: str, permission: str) -> bool:
    return config["roles"].get(role, {}).get(permission, False)

# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="トポロジー可視化", layout="wide")

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

        if can(config, role, "can_view_topology"):
            render_topology_page()
        else:
            st.error("🔒 このページを閲覧する権限がありません（管理者のみ利用可能です）")

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()