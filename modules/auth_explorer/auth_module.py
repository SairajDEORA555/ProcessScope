"""Module 8 - Authentication (Kerberos, NTLM, PAM, SSH).

Steps through each protocol's message exchange with a communication diagram and
maps every step to the attack that targets it.
"""
import time
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.auth_explorer.auth_model import AuthRepository, AuthFlowModel, AuthStep

_P = AppConfig.PALETTE


class AuthExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = AuthRepository.from_json(JsonDataLoader(), "auth_flows.json")

    @property
    def id(self) -> str:
        return "auth_explorer"

    @property
    def title(self) -> str:
        return "Authentication"

    @property
    def icon(self) -> str:
        return "\U0001f510"

    @property
    def description(self) -> str:
        return "Walk the Kerberos, NTLM, PAM and SSH flows - and the attacks that target each step."

    # ---- entry point ----
    def render(self) -> None:
        protocols = self._repo.protocols()
        st.session_state.setdefault("auth_proto", protocols[0].key)
        st.session_state.setdefault("auth_step", 0)
        page_header("Authentication", self.description, pill="Module 8")

        self._render_proto_switch(protocols)
        flow = self._repo.get(AppState.get("auth_proto")) or protocols[0]
        if AppState.get("auth_step") >= len(flow.steps):
            AppState.set("auth_step", 0)

        self._render_metrics(flow)

        left, right = st.columns([1, 1.4], gap="large")
        with left:
            self._render_step_list(flow)
            self._render_controls(flow)
        with right:
            self._render_diagram(flow)
            self._render_detail(flow.steps[AppState.get("auth_step")])
            self._render_attacks(flow)

    # ---- protocol switch ----
    def _render_proto_switch(self, protocols) -> None:
        cols = st.columns(len(protocols))
        for col, flow in zip(cols, protocols):
            with col:
                active = flow.key == AppState.get("auth_proto")
                if st.button(flow.label, key=f"auth_p_{flow.key}",
                             type="primary" if active else "secondary",
                             use_container_width=True):
                    AppState.set("auth_proto", flow.key)
                    AppState.set("auth_step", 0)
                    st.rerun()

    # ---- metrics ----
    def _render_metrics(self, flow: AuthFlowModel) -> None:
        metric_cards([
            ("Steps", str(len(flow.steps)), _P.accent),
            ("Actors", str(len(flow.actors)), _P.info),
            ("Related attacks", str(len(flow.attacks)), _P.danger),
        ])

    # ---- step list ----
    def _render_step_list(self, flow: AuthFlowModel) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Exchange steps</div>',
                    unsafe_allow_html=True)
        cur = AppState.get("auth_step")
        for i, s in enumerate(flow.steps):
            active = i == cur
            if st.button(f"{s.order}.  {s.name}", key=f"auth_s_{flow.key}_{i}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("auth_step", i)
                st.rerun()

    # ---- controls ----
    def _render_controls(self, flow: AuthFlowModel) -> None:
        st.markdown("<div style='height:.4rem;'></div>", unsafe_allow_html=True)
        cur = AppState.get("auth_step")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Prev", use_container_width=True, disabled=cur == 0):
                AppState.set("auth_step", cur - 1)
                st.rerun()
        with c2:
            if st.button("Next", use_container_width=True, disabled=cur == len(flow.steps) - 1):
                AppState.set("auth_step", cur + 1)
                st.rerun()
        with c3:
            if st.button("Play", type="primary", use_container_width=True):
                self._play(flow)

    def _play(self, flow: AuthFlowModel) -> None:
        bar = st.progress(0.0, text="Authenticating...")
        n = len(flow.steps)
        for i in range(n):
            AppState.set("auth_step", i)
            bar.progress((i + 1) / n, text=f"[{flow.steps[i].order}] {flow.steps[i].name}")
            time.sleep(0.7)
        st.rerun()

    # ---- communication diagram ----
    def _render_diagram(self, flow: AuthFlowModel) -> None:
        cur = AppState.get("auth_step")
        cur_step = flow.steps[cur]
        highlight = {cur_step.actor_from, cur_step.actor_to}

        nodes = []
        for a in flow.actors:
            hot = a["id"] in highlight
            fill = _P.accent if hot else _P.surface_alt
            font = "#ffffff" if hot else _P.text
            nodes.append(
                f'"{a["id"]}" [label="{a["label"]}", shape=box, style="rounded,filled", '
                f'fillcolor="{fill}", fontcolor="{font}", color="{_P.border}", '
                f'fontname="Inter", fontsize=10];'
            )
        edges = []
        for i, s in enumerate(flow.steps):
            is_cur = i == cur
            color = _P.accent if is_cur else "#9aa4b0"
            width = "2.4" if is_cur else "1"
            fontcolor = _P.accent if is_cur else _P.text_muted
            edges.append(
                f'"{s.actor_from}" -> "{s.actor_to}" [label="{s.order}", '
                f'color="{color}", penwidth={width}, fontcolor="{fontcolor}", '
                f'fontname="Inter", fontsize=9, arrowsize=0.6];'
            )
        dot = ('digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.3; ranksep=0.8; '
               + " ".join(nodes) + " " + " ".join(edges) + "}")
        st.graphviz_chart(dot, use_container_width=True)

    # ---- step detail ----
    def _render_detail(self, s: AuthStep) -> None:
        attack_badge = status_badge(s.attack, "critical") if s.attack else ""
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span class="ps-pill">Step {s.order}</span>
                <span style="font-weight:700;font-size:1.1rem;">{s.name}</span>
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">Message</div>
              <div style="margin-bottom:.5rem;"><code>{s.message}</code></div>
              <div class="ps-kv">What happens</div>
              <div style="margin-bottom:.5rem;">{s.description}</div>
              <div style="background:rgba(239,68,68,.12);border-left:3px solid {_P.danger};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{_P.danger};">Attack surface &nbsp; {attack_badge}</div>
                <div style="font-size:.9rem;">{s.security_note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- related attacks ----
    def _render_attacks(self, flow: AuthFlowModel) -> None:
        with st.expander(f"Related attacks ({len(flow.attacks)})"):
            for a in flow.attacks:
                st.markdown(
                    f'<div class="ps-card" style="margin-bottom:.6rem;">'
                    f'<div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">'
                    f'<span style="font-weight:700;">{a["name"]}</span>'
                    f'{status_badge(a["mitre"], "critical")}</div>'
                    f'<div style="font-size:.9rem;color:{_P.text};margin-top:.3rem;">{a["note"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
