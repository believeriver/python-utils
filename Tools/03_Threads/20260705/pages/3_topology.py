"""
Streamlit ページ: ネットワークトポロジー可視化
- CDPネイバー情報(DB)を元にスイッチ間の接続関係をグラフ表示
- YAML ベースのユーザー認証（既存ページと共通）
"""

from __future__ import annotations
import sys
from pathlib import Path

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
    "edge": "#3498db",     # 青
    "floor": "#2ecc71",    # 緑
}
UNKNOWN_COLOR = "#95a5a6"  # グレー(未解決の機器)


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

def build_graph_elements(nodes: list, edges: list, role_map: dict, show_labels: bool = False):
    agraph_nodes = []
    for n in nodes:
        hostname = n["hostname"]
        if n["resolved"]:
            role = role_map.get(hostname, "edge")
            color = ROLE_COLORS.get(role, ROLE_COLORS["edge"])
            size = 25 if role == "core" else 18
        else:
            color = UNKNOWN_COLOR
            size = 10
        agraph_nodes.append(Node(id=hostname, label=hostname, size=size, color=color))

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
    all_hostnames = sorted({n["hostname"] for n in CdpNeighbor.fetch_topology_nodes() if n["resolved"]})

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        center = st.selectbox("起点となるスイッチを選択", options=["(全体表示)"] + all_hostnames)
    with col2:
        max_hops = st.slider("表示するホップ数", min_value=1, max_value=5, value=2)
    with col3:
        show_labels = st.checkbox("ポート名を表示", value=False)

    if st.button("🔄 表示を更新"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("トポロジーデータを取得中..."):
        if center == "(全体表示)":
            nodes, edges = fetch_topology_data()
        else:
            subgraph = CdpNeighbor.fetch_topology_subgraph(center, max_hops=max_hops)
            nodes, edges = subgraph["nodes"], subgraph["edges"]
        role_map = fetch_switch_roles()

    if not nodes:
        st.warning("該当するトポロジーデータがありません。")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("表示中のノード数", len(nodes))
    m2.metric("表示中のリンク数", len(edges))
    unresolved_count = sum(1 for n in nodes if not n["resolved"])
    m3.metric("未識別の機器", unresolved_count)

    st.divider()

    agraph_nodes, agraph_edges = build_graph_elements(nodes, edges, role_map, show_labels)

    config = Config(width=1000, height=650, directed=False, physics=True, hierarchical=False)
    agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

    st.divider()
    st.caption(
        "🔴 コアスイッチ　🔵 エッジスイッチ　🟢 フロアスイッチ　⚪ 未識別の機器（IP電話・AP等）　"
        "点線 = 片側からのみ確認されたリンク"
    )


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
        with st.sidebar:
            role = get_role(config, username)
            st.markdown(f"**👤 {name}**")
            st.caption(f"ロール: `{role}`")
            st.divider()
            authenticator.logout("ログアウト", location="sidebar")

        render_topology_page()

    elif auth_status is False:
        st.error("❌ ユーザー名またはパスワードが正しくありません")
    else:
        st.info("ユーザー名とパスワードを入力してください")


if __name__ == "__main__":
    main()