"""Module 2 - Interactive Process Explorer.

Renders the parent/child process tree, a live flow diagram, and a detail panel
that teaches what each process is and why it matters to a defender.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.process_explorer.process_model import ProcessRepository, ProcessModel

_P = AppConfig.PALETTE

# Semantic badge colour per integrity level (presentation only).
INTEGRITY_BADGE = {"System": "info", "High": "warning", "Medium": "neutral", "Low": "neutral"}


class ProcessExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = ProcessRepository.from_json(JsonDataLoader(), "processes_windows.json")

    @property
    def id(self) -> str:
        return "process_explorer"

    @property
    def title(self) -> str:
        return "Process Explorer"

    @property
    def icon(self) -> str:
        return "\U0001f5a5"

    @property
    def description(self) -> str:
        return "Explore the process tree - parents, children, integrity levels and command lines."

    # ---- entry point ----
    def render(self) -> None:
        st.session_state.setdefault("pe_selected_pid", 2100)
        page_header("Process Explorer", self.description, pill="Module 2")

        self._render_metrics()
        query = st.text_input("Search processes",
                              placeholder="Name, PID, or command line...",
                              key="pe_query").strip()

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            if query:
                self._render_search_results(query)
            else:
                self._render_tree()
        with right:
            selected = self._repo.get(AppState.get("pe_selected_pid"))
            if selected is None:
                st.info("Select a process to see its details.")
            else:
                self._render_diagram(selected)
                self._render_detail(selected)

    def _select(self, pid: int) -> None:
        AppState.set("pe_selected_pid", pid)

    # ---- metrics (shared design-system helper) ----
    def _render_metrics(self) -> None:
        procs = self._repo.all()
        total = len(procs)
        signed = sum(1 for p in procs if p.signed)
        privileged = sum(1 for p in procs if p.integrity in ("System", "High"))
        metric_cards([
            ("Processes", str(total), _P.accent),
            ("Signed", f"{signed}/{total}", _P.success),
            ("System / High integrity", str(privileged), _P.warning),
        ])

    # ---- tree (recursive, cycle-guarded) ----
    def _render_tree(self) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Process Tree</div>',
                    unsafe_allow_html=True)
        for root in self._repo.roots():
            self._render_node(root, 0, set())

    def _render_node(self, proc: ProcessModel, depth: int, visited: set) -> None:
        if proc.pid in visited:
            return
        visited.add(proc.pid)
        active = proc.pid == AppState.get("pe_selected_pid")
        label = f"{self._prefix(depth)}{proc.name}  \u00b7  {proc.pid}"
        if st.button(label, key=f"pe_node_{proc.pid}",
                     type="primary" if active else "secondary",
                     use_container_width=True):
            self._select(proc.pid)
            st.rerun()
        for child in self._repo.children(proc.pid):
            self._render_node(child, depth + 1, visited)

    @staticmethod
    def _prefix(depth: int) -> str:
        if depth == 0:
            return ""
        return "\u2502  " * (depth - 1) + "\u2514\u2500 "

    # ---- search results (flat list) ----
    def _render_search_results(self, query: str) -> None:
        q = query.lower()
        matches = [p for p in self._repo.all()
                   if q in p.name.lower() or q in p.command_line.lower() or q in str(p.pid)]
        st.markdown(f'<div class="ps-kv" style="margin:.4rem 0 .5rem;">'
                    f'{len(matches)} match(es)</div>', unsafe_allow_html=True)
        for p in matches:
            active = p.pid == AppState.get("pe_selected_pid")
            if st.button(f"{p.name}  \u00b7  {p.pid}", key=f"pe_search_{p.pid}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                self._select(p.pid)
                st.rerun()
        if not matches:
            st.caption("No processes match your search.")

    # ---- flow diagram (full tree, selected highlighted) ----
    def _render_diagram(self, selected: ProcessModel) -> None:
        pids = {p.pid for p in self._repo.all()}
        nodes, edges = [], []
        for p in self._repo.all():
            is_sel = p.pid == selected.pid
            fill = _P.accent if is_sel else _P.surface_alt
            font = "#ffffff" if is_sel else _P.text
            nodes.append(
                f'"{p.pid}" [label="{p.name}\\n{p.pid}", shape=box, '
                f'style="rounded,filled", fillcolor="{fill}", fontcolor="{font}", '
                f'color="{_P.border}", fontname="Inter", fontsize=10];'
            )
            if p.ppid in pids:
                edges.append(f'"{p.ppid}" -> "{p.pid}";')
        dot = (
            'digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.16; ranksep=0.5; '
            'edge [color="#9aa4b0", arrowsize=0.6]; '
            + " ".join(nodes) + " " + " ".join(edges) + "}"
        )
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail panel (design-system node card) ----
    def _render_detail(self, p: ProcessModel) -> None:
        parent = self._repo.get(p.ppid)
        parent_txt = f"{parent.name} ({parent.pid})" if parent else f"PID {p.ppid} (not running / exited)"
        sign_txt = "Signed" if p.signed else "Unsigned"
        badges = (
            status_badge(f"PID {p.pid}", "info") + " "
            + status_badge(p.integrity, INTEGRITY_BADGE.get(p.integrity, "neutral")) + " "
            + status_badge(sign_txt, "success" if p.signed else "critical")
        )
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.15rem;">{p.name}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.8rem;">Parent process</div>
              <div style="margin-bottom:.5rem;">{parent_txt}</div>
              <div class="ps-kv">User context</div>
              <div style="margin-bottom:.5rem;">{p.user}</div>
              <div class="ps-kv">Image path</div>
              <div style="margin-bottom:.5rem;"><code>{p.path}</code></div>
              <div class="ps-kv">Command line</div>
              <div style="margin-bottom:.5rem;"><code>{p.command_line}</code></div>
              <div class="ps-kv">What it does</div>
              <div style="margin-bottom:.5rem;">{p.description}</div>
              <div style="background:{_P.accent_soft};border-left:3px solid {_P.accent};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{_P.accent};">Typical parent: {p.typical_parent}</div>
                <div style="font-size:.9rem;">{p.security_note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
