"""Module 3 - Service Explorer.

Browse Windows services with start type, account, hosting svchost group and a
dependency graph, each annotated with its security relevance for defenders.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.service_explorer.service_model import ServiceRepository, ServiceModel

_P = AppConfig.PALETTE

STATUS_BADGE = {"Running": "success", "Stopped": "neutral"}
START_BADGE = {
    "Automatic": "info",
    "Automatic (Delayed)": "info",
    "Manual": "neutral",
    "Disabled": "critical",
}


class ServiceExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = ServiceRepository.from_json(JsonDataLoader(), "services_windows.json")

    @property
    def id(self) -> str:
        return "service_explorer"

    @property
    def title(self) -> str:
        return "Service Explorer"

    @property
    def icon(self) -> str:
        return "\u2699"

    @property
    def description(self) -> str:
        return "Browse Windows services - start type, account, host group and dependencies."

    # ---- entry point ----
    def render(self) -> None:
        st.session_state.setdefault("se_selected", "Spooler")
        page_header("Service Explorer", self.description, pill="Module 3")

        self._render_metrics()

        c1, c2 = st.columns([1, 2])
        with c1:
            start_filter = st.selectbox(
                "Start type",
                ["All", "Automatic", "Automatic (Delayed)", "Manual", "Disabled"],
                key="se_start",
            )
        with c2:
            query = st.text_input("Search services",
                                  placeholder="Name, display name, or description...",
                                  key="se_query").strip()

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            self._render_list(start_filter, query)
        with right:
            svc = self._repo.get(AppState.get("se_selected"))
            if svc is None:
                st.info("Select a service to see its details.")
            else:
                self._render_diagram(svc)
                self._render_detail(svc)

    # ---- metrics ----
    def _render_metrics(self) -> None:
        svcs = self._repo.all()
        total = len(svcs)
        running = sum(1 for s in svcs if s.status == "Running")
        auto = sum(1 for s in svcs if s.start_type.startswith("Automatic"))
        metric_cards([
            ("Services", str(total), _P.accent),
            ("Running", str(running), _P.success),
            ("Auto-start", str(auto), _P.warning),
        ])

    # ---- list ----
    def _render_list(self, start_filter: str, query: str) -> None:
        services = self._repo.all()
        if start_filter != "All":
            services = [s for s in services if s.start_type == start_filter]
        if query:
            q = query.lower()
            services = [s for s in services
                        if q in s.name.lower() or q in s.display_name.lower()
                        or q in s.description.lower()]
        services = sorted(services, key=lambda s: s.display_name)

        st.markdown(f'<div class="ps-kv" style="margin:.2rem 0 .5rem;">'
                    f'{len(services)} service(s)</div>', unsafe_allow_html=True)
        for s in services:
            dot = "\u25cf" if s.status == "Running" else "\u25cb"
            active = s.name == AppState.get("se_selected")
            if st.button(f"{dot}  {s.display_name}", key=f"se_{s.name}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("se_selected", s.name)
                st.rerun()
        if not services:
            st.caption("No services match your filters.")

    # ---- dependency diagram ----
    def _render_diagram(self, svc: ServiceModel) -> None:
        seen: set = set()
        nodes, edges = [], []

        def add_node(name: str, label: str, highlight: bool = False) -> None:
            if name in seen:
                return
            seen.add(name)
            fill = _P.accent if highlight else _P.surface_alt
            font = "#ffffff" if highlight else _P.text
            nodes.append(
                f'"{name}" [label="{label}", shape=box, style="rounded,filled", '
                f'fillcolor="{fill}", fontcolor="{font}", color="{_P.border}", '
                f'fontname="Inter", fontsize=10];'
            )

        add_node(svc.name, svc.display_name, highlight=True)
        for dep_name in svc.dependencies:
            dep = self._repo.get(dep_name)
            add_node(dep_name, dep.display_name if dep else dep_name)
            edges.append(f'"{dep_name}" -> "{svc.name}";')
        for dependent in self._repo.dependents(svc.name):
            add_node(dependent.name, dependent.display_name)
            edges.append(f'"{svc.name}" -> "{dependent.name}";')

        dot = (
            'digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.2; ranksep=0.5; '
            'edge [color="#9aa4b0", arrowsize=0.6]; '
            + " ".join(nodes) + " " + " ".join(edges) + "}"
        )
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail panel (design-system node card) ----
    def _render_detail(self, s: ServiceModel) -> None:
        deps = ", ".join(s.dependencies) if s.dependencies else "None"
        pid_txt = str(s.hosting_pid) if s.hosting_pid and s.hosting_pid > 0 else "Not running"
        badges = (
            status_badge(s.status, STATUS_BADGE.get(s.status, "neutral")) + " "
            + status_badge(s.start_type, START_BADGE.get(s.start_type, "neutral"))
        )
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.15rem;">{s.display_name}</span>
                <span class="ps-pill">{s.name}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.8rem;">Runs as</div>
              <div style="margin-bottom:.5rem;">{s.account}</div>
              <div class="ps-kv">Binary path</div>
              <div style="margin-bottom:.5rem;"><code>{s.binary_path}</code></div>
              <div class="ps-kv">Host group / Hosting PID</div>
              <div style="margin-bottom:.5rem;">{s.host_group} &nbsp;&middot;&nbsp; PID {pid_txt}</div>
              <div class="ps-kv">Depends on</div>
              <div style="margin-bottom:.5rem;">{deps}</div>
              <div class="ps-kv">What it does</div>
              <div style="margin-bottom:.5rem;">{s.description}</div>
              <div style="background:{_P.accent_soft};border-left:3px solid {_P.accent};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{_P.accent};">Security relevance</div>
                <div style="font-size:.9rem;">{s.security_note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
