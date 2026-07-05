"""Module 4 - Driver Explorer.

Browse kernel-mode drivers with type, signer, start type and the hardware they
serve, each annotated with its Ring 0 security relevance (BYOVD, DSE, filters).
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.driver_explorer.driver_model import DriverRepository, DriverModel

_P = AppConfig.PALETTE

STATUS_BADGE = {"Running": "success", "Stopped": "neutral"}
START_BADGE = {
    "Boot": "info",
    "System": "info",
    "Automatic": "neutral",
    "Manual": "neutral",
    "Disabled": "critical",
}


class DriverExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = DriverRepository.from_json(JsonDataLoader(), "drivers_windows.json")

    @property
    def id(self) -> str:
        return "driver_explorer"

    @property
    def title(self) -> str:
        return "Driver Explorer"

    @property
    def icon(self) -> str:
        return "\U0001f50c"

    @property
    def description(self) -> str:
        return "Inspect kernel-mode drivers - type, signer, start order and the hardware they serve."

    # ---- entry point ----
    def render(self) -> None:
        st.session_state.setdefault("de_selected", "ntfs.sys")
        page_header("Driver Explorer", self.description, pill="Module 4")

        self._render_metrics()

        c1, c2 = st.columns([1, 2])
        with c1:
            type_filter = st.selectbox("Driver type", ["All"] + self._repo.types(), key="de_type")
        with c2:
            query = st.text_input("Search drivers",
                                  placeholder="Name, signer, or hardware...",
                                  key="de_query").strip()

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            self._render_list(type_filter, query)
        with right:
            drv = self._repo.get(AppState.get("de_selected"))
            if drv is None:
                st.info("Select a driver to see its details.")
            else:
                self._render_diagram(drv)
                self._render_detail(drv)

    # ---- metrics ----
    def _render_metrics(self) -> None:
        drivers = self._repo.all()
        total = len(drivers)
        signed = sum(1 for d in drivers if d.signed)
        boot = sum(1 for d in drivers if d.start_type == "Boot")
        metric_cards([
            ("Drivers", str(total), _P.accent),
            ("Signed", f"{signed}/{total}", _P.success),
            ("Boot-start", str(boot), _P.warning),
        ])

    # ---- list ----
    def _render_list(self, type_filter: str, query: str) -> None:
        drivers = self._repo.all()
        if type_filter != "All":
            drivers = [d for d in drivers if d.driver_type == type_filter]
        if query:
            q = query.lower()
            drivers = [d for d in drivers
                       if q in d.name.lower() or q in d.display_name.lower()
                       or q in d.signer.lower() or q in d.hardware.lower()]
        drivers = sorted(drivers, key=lambda d: d.display_name)

        st.markdown(f'<div class="ps-kv" style="margin:.2rem 0 .5rem;">'
                    f'{len(drivers)} driver(s)</div>', unsafe_allow_html=True)
        for d in drivers:
            dot = "\u25cf" if d.status == "Running" else "\u25cb"
            active = d.name == AppState.get("de_selected")
            if st.button(f"{dot}  {d.display_name}", key=f"de_{d.name}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("de_selected", d.name)
                st.rerun()
        if not drivers:
            st.caption("No drivers match your filters.")

    # ---- Ring 0 position diagram: Hardware -> Driver -> Kernel ----
    def _render_diagram(self, d: DriverModel) -> None:
        def node(nid, label, highlight=False):
            fill = _P.accent if highlight else _P.surface_alt
            font = "#ffffff" if highlight else _P.text
            return (f'"{nid}" [label="{label}", shape=box, style="rounded,filled", '
                    f'fillcolor="{fill}", fontcolor="{font}", color="{_P.border}", '
                    f'fontname="Inter", fontsize=10];')

        nodes = [
            node("hw", d.hardware),
            node("drv", d.name, highlight=True),
            node("krnl", "Windows Kernel (Ring 0)"),
        ]
        edges = ['"hw" -> "drv";', '"drv" -> "krnl";']
        dot = (
            'digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.25; ranksep=0.6; '
            'edge [color="#9aa4b0", arrowsize=0.6]; '
            + " ".join(nodes) + " " + " ".join(edges) + "}"
        )
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail panel ----
    def _render_detail(self, d: DriverModel) -> None:
        sign_txt = "Signed" if d.signed else "Unsigned"
        badges = (
            status_badge(d.driver_type, "neutral") + " "
            + status_badge(sign_txt, "success" if d.signed else "critical") + " "
            + status_badge(d.status, STATUS_BADGE.get(d.status, "neutral")) + " "
            + status_badge(d.start_type, START_BADGE.get(d.start_type, "neutral"))
        )
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.15rem;">{d.display_name}</span>
                <span class="ps-pill">{d.name}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.8rem;">Signed by</div>
              <div style="margin-bottom:.5rem;">{d.signer}</div>
              <div class="ps-kv">Image path</div>
              <div style="margin-bottom:.5rem;"><code>{d.path}</code></div>
              <div class="ps-kv">Load group / Start type</div>
              <div style="margin-bottom:.5rem;">{d.load_group} &nbsp;&middot;&nbsp; {d.start_type}-start</div>
              <div class="ps-kv">Hardware / subsystem</div>
              <div style="margin-bottom:.5rem;">{d.hardware}</div>
              <div class="ps-kv">What it does</div>
              <div style="margin-bottom:.5rem;">{d.description}</div>
              <div style="background:{_P.accent_soft};border-left:3px solid {_P.accent};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{_P.accent};">Ring 0 security relevance</div>
                <div style="font-size:.9rem;">{d.security_note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
