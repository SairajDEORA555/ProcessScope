"""Module 7 - Networking Visualization.

Lists host connections (listeners vs established) and draws a per-process graph
of remote endpoints, flagging the C2/exfil/lateral-movement patterns in red.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.network_explorer.connection_model import ConnectionRepository, ConnectionModel

_P = AppConfig.PALETTE

STATE_BADGE = {"ESTABLISHED": "success", "LISTENING": "info"}


class NetworkExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = ConnectionRepository.from_json(JsonDataLoader(), "connections.json")

    @property
    def id(self) -> str:
        return "network_explorer"

    @property
    def title(self) -> str:
        return "Network Explorer"

    @property
    def icon(self) -> str:
        return "\U0001f310"

    @property
    def description(self) -> str:
        return "Inspect host connections and each process's network footprint - listeners, C2 and exfil."

    # ---- entry point ----
    def render(self) -> None:
        st.session_state.setdefault("net_selected", 0)
        page_header("Network Explorer", self.description, pill="Module 7")

        self._render_metrics()

        c1, c2 = st.columns([1, 2])
        with c1:
            view = st.selectbox("View", ["All", "Listening", "Established", "Suspicious"], key="net_view")
        with c2:
            query = st.text_input("Search connections",
                                  placeholder="Process, remote address, port, or service...",
                                  key="net_query").strip()

        left, right = st.columns([1, 1.4], gap="large")
        with left:
            self._render_list(view, query)
        with right:
            sel = self._repo.get(AppState.get("net_selected"))
            if sel is None:
                st.info("Select a connection to see its details.")
            else:
                self._render_graph(sel)
                self._render_detail(sel)

    # ---- metrics ----
    def _render_metrics(self) -> None:
        conns = self._repo.all()
        total = len(conns)
        established = sum(1 for c in conns if c.state == "ESTABLISHED")
        suspicious = sum(1 for c in conns if c.suspicious)
        metric_cards([
            ("Connections", str(total), _P.accent),
            ("Established", str(established), _P.success),
            ("Suspicious", str(suspicious), _P.danger),
        ])

    # ---- list ----
    def _render_list(self, view: str, query: str) -> None:
        q = query.lower()

        def match(c: ConnectionModel) -> bool:
            if view == "Listening" and c.state != "LISTENING":
                return False
            if view == "Established" and c.state != "ESTABLISHED":
                return False
            if view == "Suspicious" and not c.suspicious:
                return False
            if q:
                hay = f"{c.process} {c.remote_addr} {c.remote_port} {c.local_port} {c.service}".lower()
                if q not in hay:
                    return False
            return True

        shown = [(i, c) for i, c in enumerate(self._repo.all()) if match(c)]
        st.markdown(f'<div class="ps-kv" style="margin:.2rem 0 .5rem;">'
                    f'{len(shown)} connection(s)</div>', unsafe_allow_html=True)
        for i, c in shown:
            mark = "  \u26a0" if c.suspicious else ""
            active = i == AppState.get("net_selected")
            if c.state == "LISTENING":
                label = f"{c.process}  \u00b7  :{c.local_port} LISTEN{mark}"
            else:
                label = f"{c.process}  \u00b7  {c.remote_addr}:{c.remote_port}{mark}"
            if st.button(label, key=f"net_{i}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("net_selected", i)
                st.rerun()
        if not shown:
            st.caption("No connections match your filters.")

    # ---- per-process endpoint graph ----
    def _render_graph(self, sel: ConnectionModel) -> None:
        peers = self._repo.by_pid(sel.pid)
        proc_id = f"proc_{sel.pid}"
        nodes = [
            f'"{proc_id}" [label="{sel.process}\\nPID {sel.pid}", shape=box, '
            f'style="rounded,filled", fillcolor="{_P.accent}", fontcolor="#ffffff", '
            f'color="{_P.border}", fontname="Inter", fontsize=10];'
        ]
        seen_nodes, seen_edges = set(), set()
        for c in peers:
            ep = c.endpoint()
            if ep not in seen_nodes:
                seen_nodes.add(ep)
                fill = _P.danger if c.suspicious else _P.surface_alt
                font = "#ffffff" if c.suspicious else _P.text
                line_w = "2.4" if ep == sel.endpoint() else "1"
                nodes.append(
                    f'"{ep}" [label="{ep}", shape=box, style="rounded,filled", '
                    f'fillcolor="{fill}", fontcolor="{font}", color="{_P.text if ep == sel.endpoint() else _P.border}", '
                    f'penwidth={line_w}, fontname="Inter", fontsize=10];'
                )
            ekey = (proc_id, ep, c.service)
            if ekey not in seen_edges:
                seen_edges.add(ekey)
                nodes.append(f'"{proc_id}" -> "{ep}" [label="{c.service}", '
                             f'fontname="Inter", fontsize=8, fontcolor="{_P.text_muted}"];')
        dot = ('digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.25; ranksep=0.7; '
               'edge [color="#9aa4b0", arrowsize=0.6]; ' + " ".join(nodes) + "}")
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail panel ----
    def _render_detail(self, c: ConnectionModel) -> None:
        badges = status_badge(c.protocol, "neutral") + " " + status_badge(
            c.state if c.state else "STATELESS", STATE_BADGE.get(c.state, "neutral"))
        if c.suspicious:
            badges += " " + status_badge("Suspicious", "critical")
        box_color = _P.danger if c.suspicious else _P.accent
        box_bg = "rgba(239,68,68,.12)" if c.suspicious else _P.accent_soft
        remote = "*" if c.remote_addr == "*" else f"{c.remote_addr}:{c.remote_port}"
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.05rem;">{c.service or c.protocol}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">Owning process</div>
              <div style="margin-bottom:.5rem;">{c.process} (PID {c.pid})</div>
              <div class="ps-kv">Local endpoint</div>
              <div style="margin-bottom:.5rem;"><code>{c.local_addr}:{c.local_port}</code></div>
              <div class="ps-kv">Remote endpoint / Direction</div>
              <div style="margin-bottom:.5rem;"><code>{remote}</code> &nbsp;&middot;&nbsp; {c.direction}</div>
              <div style="background:{box_bg};border-left:3px solid {box_color};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{box_color};">Security relevance</div>
                <div style="font-size:.9rem;">{c.note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
