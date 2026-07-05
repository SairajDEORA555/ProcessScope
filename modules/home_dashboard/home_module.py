"""Home / Dashboard - a platform overview with live incident status,
KPI cards, and a quick-launch module catalog.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from core.telemetry import TelemetryStore

_P = AppConfig.PALETTE

SEV_WEIGHT = {"Critical": 45, "High": 25, "Medium": 10}
SEV_BADGE = {"Critical": "critical", "High": "warning", "Medium": "neutral"}

CATALOG = [
    ("Explore the OS", [
        ("boot_simulator", "\u26a1", "Boot Simulator"),
        ("process_explorer", "\U0001f5a5", "Process Explorer"),
        ("service_explorer", "\u2699", "Service Explorer"),
        ("driver_explorer", "\U0001f50c", "Driver Explorer"),
        ("registry_explorer", "\U0001f5c4", "Registry Explorer"),
        ("memory_explorer", "\U0001f4be", "Memory Explorer"),
        ("network_explorer", "\U0001f310", "Network Explorer"),
        ("auth_explorer", "\U0001f510", "Authentication"),
        ("proctree_explorer", "\U0001f333", "Process Trees"),
    ]),
    ("Attack & Defense", [
        ("attack_simulator", "\u2694", "Attack Simulator"),
        ("edr_console", "\U0001f6e1", "EDR Console"),
        ("soc_workspace", "\U0001f50e", "SOC Workspace"),
    ]),
    ("Reference", [
        ("global_search", "\U0001f50d", "Global Search"),
        ("learning_center", "\U0001f4d8", "Learning Center"),
    ]),
]


class HomeDashboardModule(BaseModule):
    def __init__(self) -> None:
        loader = JsonDataLoader()
        try:
            self._n_attacks = len(loader.load("attacks.json"))
        except Exception:
            self._n_attacks = 0
        try:
            self._n_topics = len(loader.load("learning.json"))
        except Exception:
            self._n_topics = 0
        self._n_modules = sum(len(items) for _, items in CATALOG) + 1

    @property
    def id(self) -> str:
        return "home_dashboard"

    @property
    def title(self) -> str:
        return "Dashboard"

    @property
    def icon(self) -> str:
        return "\U0001f3e0"

    @property
    def description(self) -> str:
        return "Operating System Internals, Attack & Defense - at a glance."

    # ---- entry point ----
    def render(self) -> None:
        page_header("ProcessScope Dashboard", self.description, pill="Home")
        self._render_incident()
        self._render_kpis()
        self._render_catalog()
        self._render_recent()

    # ---- live incident status ----
    def _render_incident(self) -> None:
        alerts = TelemetryStore.alerts()
        isolated = AppState.get("edr_isolated", False)
        if not alerts:
            st.markdown(
                f'<div class="ps-card" style="background:rgba(34,197,94,.10);'
                f'border-left:3px solid {_P.success};">'
                f'<span style="font-weight:700;color:{_P.success};">Environment clean</span>'
                f'<span style="color:{_P.text_muted};"> &nbsp;&middot;&nbsp; No active incident. '
                f'Run attacks in the Attack Simulator to generate telemetry.</span></div>',
                unsafe_allow_html=True,
            )
            return
        score = min(100, sum(SEV_WEIGHT.get(a["severity"], 0) for a in alerts))
        if score < 40:
            level, color = "Guarded", _P.info
        elif score < 70:
            level, color = "Elevated", _P.warning
        else:
            level, color = "Critical", _P.danger
        host = ("Isolated", "critical") if isolated else ("Online", "success")
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;">
                <span style="font-size:1.8rem;font-weight:800;color:{color};">{score}</span>
                <span class="ps-kv">/ 100 risk</span>
                {status_badge(level, {"Guarded":"info","Elevated":"warning","Critical":"critical"}[level])}
                <span style="margin-left:auto;">Host DESKTOP-PS {status_badge(host[0], host[1])}</span>
              </div>
              <div style="height:8px;background:{_P.border};border-radius:999px;overflow:hidden;margin-top:.6rem;">
                <div style="width:{score}%;height:100%;background:{color};border-radius:999px;"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- KPI cards ----
    def _render_kpis(self) -> None:
        metric_cards([
            ("Modules", str(self._n_modules), _P.accent),
            ("Attacks", str(self._n_attacks), _P.warning),
            ("Learning topics", str(self._n_topics), _P.info),
            ("Live alerts", str(len(TelemetryStore.alerts())), _P.danger),
        ])

    # ---- module catalog (quick launch) ----
    def _render_catalog(self) -> None:
        for group, items in CATALOG:
            st.markdown(f'<div class="ps-kv" style="margin:.9rem 0 .5rem;">{group}</div>',
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (mid, icon, title) in enumerate(items):
                with cols[i % 3]:
                    if st.button(f"{icon}  {title}", key=f"home_{mid}", use_container_width=True):
                        AppState.set("active_module", mid)
                        st.rerun()

    # ---- recent alerts ----
    def _render_recent(self) -> None:
        alerts = TelemetryStore.alerts()
        if not alerts:
            return
        st.markdown('<div class="ps-kv" style="margin:.9rem 0 .5rem;">Recent detections</div>',
                    unsafe_allow_html=True)
        for a in alerts[-5:][::-1]:
            st.markdown(
                f'<div style="padding:.35rem 0;border-bottom:1px solid {_P.surface_alt};">'
                f'{status_badge(a["severity"], SEV_BADGE.get(a["severity"], "neutral"))} '
                f'&nbsp;<strong>{a["name"]}</strong> '
                f'<span class="ps-kv">{a["technique"]} &middot; {a["time"]}</span></div>',
                unsafe_allow_html=True,
            )
        if st.button("Open EDR Console", type="primary"):
            AppState.set("active_module", "edr_console")
            st.rerun()
