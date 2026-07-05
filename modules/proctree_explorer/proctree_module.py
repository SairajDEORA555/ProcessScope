"""Module 9 - Interactive Process Trees.

Compare a clean host against attack-chain scenarios, with each process scored
benign / suspicious / malicious to teach reading parent-child anomalies.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.proctree_explorer.proctree_model import ProcTreeRepository, ProcTreeScenario, ProcTreeNode

_P = AppConfig.PALETTE

VERDICT_MARK = {"benign": "", "suspicious": "  \u26a0", "malicious": "  \u2716"}
VERDICT_BADGE = {"benign": "success", "suspicious": "warning", "malicious": "critical"}
VERDICT_FILL = {"benign": _P.surface_alt, "suspicious": _P.warning, "malicious": _P.danger}
VERDICT_FONT = {"benign": _P.text, "suspicious": "#161B22", "malicious": "#ffffff"}


class ProcTreeExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = ProcTreeRepository.from_json(JsonDataLoader(), "process_tree_scenarios.json")

    @property
    def id(self) -> str:
        return "proctree_explorer"

    @property
    def title(self) -> str:
        return "Process Trees"

    @property
    def icon(self) -> str:
        return "\U0001f333"

    @property
    def description(self) -> str:
        return "Read attack chains in the process tree - scored benign, suspicious or malicious."

    # ---- entry point ----
    def render(self) -> None:
        scenarios = self._repo.scenarios()
        st.session_state.setdefault("pt_scenario", "phishing")
        page_header("Process Trees", self.description, pill="Module 9")

        self._render_scenario_switch(scenarios)
        scen = self._repo.get(AppState.get("pt_scenario")) or scenarios[0]

        self._render_banner(scen)
        self._render_metrics(scen)

        pids = {n.pid for n in scen.nodes}
        if AppState.get("pt_selected") not in pids:
            AppState.set("pt_selected", self._default_pid(scen))

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            self._render_tree(scen)
        with right:
            self._render_diagram(scen)
            self._render_detail(scen.get(AppState.get("pt_selected")))

    # ---- scenario switch ----
    def _render_scenario_switch(self, scenarios) -> None:
        cols = st.columns(len(scenarios))
        for col, scen in zip(cols, scenarios):
            with col:
                active = scen.key == AppState.get("pt_scenario")
                if st.button(scen.label, key=f"pt_s_{scen.key}",
                             type="primary" if active else "secondary",
                             use_container_width=True):
                    AppState.set("pt_scenario", scen.key)
                    AppState.set("pt_selected", None)
                    st.rerun()

    # ---- verdict banner ----
    def _render_banner(self, scen: ProcTreeScenario) -> None:
        verds = {n.verdict for n in scen.nodes}
        if "malicious" in verds:
            text, color, bg = "Compromised", _P.danger, "rgba(239,68,68,.12)"
        elif "suspicious" in verds:
            text, color, bg = "Suspicious activity", _P.warning, "rgba(245,158,11,.12)"
        else:
            text, color, bg = "Clean", _P.success, "rgba(34,197,94,.12)"
        st.markdown(
            f'<div class="ps-card" style="background:{bg};border-left:3px solid {color};">'
            f'<span style="font-weight:700;color:{color};">{text}</span>'
            f'<span style="color:{_P.text_muted};"> &nbsp;&middot;&nbsp; {scen.description}</span></div>',
            unsafe_allow_html=True,
        )

    # ---- metrics ----
    def _render_metrics(self, scen: ProcTreeScenario) -> None:
        nodes = scen.nodes
        metric_cards([
            ("Processes", str(len(nodes)), _P.accent),
            ("Suspicious", str(sum(1 for n in nodes if n.verdict == "suspicious")), _P.warning),
            ("Malicious", str(sum(1 for n in nodes if n.verdict == "malicious")), _P.danger),
        ])

    # ---- tree ----
    def _render_tree(self, scen: ProcTreeScenario) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Process Tree</div>',
                    unsafe_allow_html=True)
        for root in scen.roots():
            self._render_node(scen, root, 0, set())

    def _render_node(self, scen, node: ProcTreeNode, depth: int, visited: set) -> None:
        if node.pid in visited:
            return
        visited.add(node.pid)
        active = node.pid == AppState.get("pt_selected")
        label = f"{self._prefix(depth)}{node.name}  \u00b7  {node.pid}{VERDICT_MARK.get(node.verdict, '')}"
        if st.button(label, key=f"pt_n_{node.pid}",
                     type="primary" if active else "secondary",
                     use_container_width=True):
            AppState.set("pt_selected", node.pid)
            st.rerun()
        for child in scen.children(node.pid):
            self._render_node(scen, child, depth + 1, visited)

    @staticmethod
    def _prefix(depth: int) -> str:
        if depth == 0:
            return ""
        return "\u2502  " * (depth - 1) + "\u2514\u2500 "

    # ---- verdict-colored flow diagram ----
    def _render_diagram(self, scen: ProcTreeScenario) -> None:
        sel = AppState.get("pt_selected")
        pids = {n.pid for n in scen.nodes}
        nodes, edges = [], []
        for n in scen.nodes:
            is_sel = n.pid == sel
            fill = VERDICT_FILL.get(n.verdict, _P.surface_alt)
            font = VERDICT_FONT.get(n.verdict, _P.text)
            pen = "2.6" if is_sel else "1"
            border = _P.text if is_sel else _P.border
            nodes.append(
                f'"{n.pid}" [label="{n.name}\\n{n.pid}", shape=box, style="rounded,filled", '
                f'fillcolor="{fill}", fontcolor="{font}", color="{border}", penwidth={pen}, '
                f'fontname="Inter", fontsize=10];'
            )
            if n.ppid in pids:
                edges.append(f'"{n.ppid}" -> "{n.pid}";')
        dot = ('digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.2; ranksep=0.55; '
               'edge [color="#9aa4b0", arrowsize=0.6]; '
               + " ".join(nodes) + " " + " ".join(edges) + "}")
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail ----
    def _render_detail(self, n) -> None:
        if n is None:
            st.info("Select a process to see its analysis.")
            return
        verdict_badge = status_badge(n.verdict.capitalize(), VERDICT_BADGE.get(n.verdict, "neutral"))
        color = VERDICT_FILL.get(n.verdict, _P.accent)
        bg = {"benign": _P.accent_soft, "suspicious": "rgba(245,158,11,.12)",
              "malicious": "rgba(239,68,68,.12)"}.get(n.verdict, _P.accent_soft)
        tech = (f'<div class="ps-kv">MITRE ATT&amp;CK</div>'
                f'<div style="margin-bottom:.5rem;">{n.technique}</div>') if n.technique else ""
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.1rem;">{n.name}</span>
                <span class="ps-pill">PID {n.pid}</span>
                {verdict_badge}
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">User</div>
              <div style="margin-bottom:.5rem;">{n.user}</div>
              <div class="ps-kv">Command line</div>
              <div style="margin-bottom:.5rem;"><code>{n.cmdline}</code></div>
              {tech}
              <div style="background:{bg};border-left:3px solid {color};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{color};">Analyst verdict</div>
                <div style="font-size:.9rem;">{n.reason}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- helpers ----
    @staticmethod
    def _default_pid(scen: ProcTreeScenario) -> int:
        mal = [n for n in scen.nodes if n.verdict == "malicious"]
        if mal:
            return mal[0].pid
        return scen.roots()[0].pid
