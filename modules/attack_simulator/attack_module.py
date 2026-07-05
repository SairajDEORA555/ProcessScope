"""Module 10 - Attack Simulator.

A catalog of attacks modeled as kill-chains. Running an attack plays its stages
and writes telemetry to the TelemetryStore for the EDR and SOC modules to detect.
"""
import time
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from core.telemetry import TelemetryStore
from modules.attack_simulator.attack_model import AttackRepository, AttackModel

_P = AppConfig.PALETTE

SEV_BADGE = {"Critical": "critical", "High": "warning", "Medium": "neutral"}
SEV_MARK = {"Critical": "\u2716", "High": "\u26a0", "Medium": "\u00b7"}


class AttackSimulatorModule(BaseModule):
    def __init__(self) -> None:
        self._repo = AttackRepository.from_json(JsonDataLoader(), "attacks.json")

    @property
    def id(self) -> str:
        return "attack_simulator"

    @property
    def title(self) -> str:
        return "Attack Simulator"

    @property
    def icon(self) -> str:
        return "\u2694"

    @property
    def description(self) -> str:
        return "Run attack kill-chains that generate telemetry for the EDR and SOC modules."

    # ---- entry point ----
    def render(self) -> None:
        attacks = self._repo.all()
        st.session_state.setdefault("atk_selected", attacks[0].id)
        page_header("Attack Simulator", self.description, pill="Module 10")

        self._render_top()

        c1, c2 = st.columns([1, 2])
        with c1:
            tactic = st.selectbox("Tactic", ["All"] + self._repo.tactics(), key="atk_tactic")
        with c2:
            query = st.text_input("Search attacks",
                                  placeholder="Name, technique, or tactic...",
                                  key="atk_query").strip()

        left, right = st.columns([1, 1.5], gap="large")
        with left:
            self._render_list(tactic, query)
        with right:
            attack = self._repo.get(AppState.get("atk_selected"))
            if attack is None:
                st.info("Select an attack to see its kill-chain.")
            else:
                self._render_detail(attack)

    # ---- top metrics + reset ----
    def _render_top(self) -> None:
        metric_cards([
            ("Attacks available", str(len(self._repo.all())), _P.accent),
            ("Attacks run", str(len(TelemetryStore.attacks())), _P.warning),
            ("Alerts generated", str(len(TelemetryStore.alerts())), _P.danger),
        ])
        cols = st.columns([3, 1])
        with cols[1]:
            if st.button("Reset environment", use_container_width=True):
                TelemetryStore.clear()
                st.rerun()

    # ---- list ----
    def _render_list(self, tactic: str, query: str) -> None:
        attacks = self._repo.all()
        if tactic != "All":
            attacks = [a for a in attacks if a.tactic == tactic]
        if query:
            q = query.lower()
            attacks = [a for a in attacks
                       if q in a.name.lower() or q in a.technique.lower() or q in a.tactic.lower()]

        st.markdown(f'<div class="ps-kv" style="margin:.2rem 0 .5rem;">'
                    f'{len(attacks)} attack(s)</div>', unsafe_allow_html=True)
        for a in attacks:
            mark = SEV_MARK.get(a.severity, "")
            run = "  \u2713" if TelemetryStore.is_recorded(a.id) else ""
            active = a.id == AppState.get("atk_selected")
            if st.button(f"{mark}  {a.name}{run}", key=f"atk_{a.id}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("atk_selected", a.id)
                st.rerun()

    # ---- detail ----
    def _render_detail(self, a: AttackModel) -> None:
        stages_html = ""
        for s in a.stages:
            stages_html += (
                f'<div style="margin-bottom:.6rem;">'
                f'<span class="ps-pill">{s.order}</span> '
                f'<strong>{s.name}</strong>'
                f'<div style="margin:.25rem 0;"><code>{s.action}</code></div>'
                f'<div style="font-size:.88rem;color:{_P.text_muted};">{s.detail}</div></div>'
            )
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.2rem;">{a.name}</span>
                {status_badge(a.severity, SEV_BADGE.get(a.severity, "neutral"))}
                {status_badge(a.tactic, "info")}
                <span class="ps-pill">{a.technique}</span>
              </div>
              <div style="margin-top:.6rem;color:{_P.text};">{a.description}</div>
              <div class="ps-kv" style="margin-top:.9rem;">Kill chain</div>
              <div style="margin-top:.4rem;">{stages_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if TelemetryStore.is_recorded(a.id):
            st.success("Attack executed. Telemetry is available in the EDR Console and SOC Workspace.")
        else:
            if st.button("\u25b6 Run Attack", type="primary", key=f"run_{a.id}"):
                self._run(a)

        self._render_artifacts(a)

    def _run(self, a: AttackModel) -> None:
        bar = st.progress(0.0, text="Executing attack...")
        n = len(a.stages)
        for i, s in enumerate(a.stages):
            bar.progress((i + 1) / n, text=f"[{s.order}] {s.name}")
            time.sleep(0.6)
        TelemetryStore.record(a)
        st.rerun()

    def _render_artifacts(self, a: AttackModel) -> None:
        if a.processes:
            with st.expander(f"Generated processes ({len(a.processes)})"):
                for p in a.processes:
                    st.markdown(f'- **{p["name"]}** (PID {p["pid"]}, PPID {p["ppid"]}) '
                                f'`{p["cmdline"]}`')
        if a.connections:
            with st.expander(f"Generated connections ({len(a.connections)})"):
                for c in a.connections:
                    st.markdown(f'- **{c["process"]}** -> `{c["remote"]}:{c["port"]}` - {c["note"]}')
        if a.registry:
            with st.expander(f"Registry changes ({len(a.registry)})"):
                for r in a.registry:
                    st.markdown(f'- `{r["path"]}` -> **{r["value"]}** = `{r["data"]}`')
        with st.expander(f"Generated events ({len(a.events)})"):
            for e in a.events:
                st.markdown(f'- **{e["source"]} {e["event_id"]}** - {e["message"]}')
        with st.expander(f"Indicators of Compromise ({len(a.iocs)})"):
            for ioc in a.iocs:
                st.markdown(f'- `{ioc}`')
