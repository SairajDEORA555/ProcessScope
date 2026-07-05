"""Module 1 - Boot Simulator.

Interactive walkthrough of the Windows and Linux boot chains. The user picks an
OS, steps through each phase (or auto-plays the sequence), and sees a live flow
diagram; the per-phase details open in a centered modal dialog.
"""
import time
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header
from core.config import AppConfig
from core.state import AppState
from modules.boot_simulator.boot_data import BOOT_CHAINS, BootStage

_P = AppConfig.PALETTE


class BootSimulatorModule(BaseModule):
    @property
    def id(self) -> str:
        return "boot_simulator"

    @property
    def title(self) -> str:
        return "Boot Simulator"

    @property
    def icon(self) -> str:
        return "\u26a1"

    @property
    def description(self) -> str:
        return "Step through the Windows and Linux boot chains, phase by phase."

    # ---- state helpers (module owns its own keys) ----
    def _os(self) -> str:
        return AppState.get("bs_os", "windows")

    def _index(self) -> int:
        return AppState.get("bs_index", 0)

    def render(self) -> None:
        st.session_state.setdefault("bs_os", "windows")
        st.session_state.setdefault("bs_index", 0)

        page_header("Boot Simulator", self.description, pill="Module 1")

        self._render_os_switch()
        stages = BOOT_CHAINS[self._os()]
        self._clamp_index(stages)

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            self._render_stage_list(stages)
            self._render_controls(stages)
        with right:
            self._render_diagram(stages)
            st.caption("Click a boot phase to open its details.")

        # Open the detail modal once, right after selection changed.
        if AppState.get("bs_open"):
            AppState.set("bs_open", False)
            self._detail_dialog(stages[self._index()])

    # ---- OS selector ----
    def _render_os_switch(self) -> None:
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("Windows", type="primary" if self._os() == "windows" else "secondary",
                         use_container_width=True):
                AppState.set("bs_os", "windows"); AppState.set("bs_index", 0); st.rerun()
        with c2:
            if st.button("Linux", type="primary" if self._os() == "linux" else "secondary",
                         use_container_width=True):
                AppState.set("bs_os", "linux"); AppState.set("bs_index", 0); st.rerun()

    # ---- stage list (clickable) ----
    def _render_stage_list(self, stages) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Boot Phases</div>',
                    unsafe_allow_html=True)
        for i, stage in enumerate(stages):
            active = i == self._index()
            if st.button(f"{stage.order}.  {stage.name}",
                         key=f"bs_stage_{self._os()}_{i}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("bs_index", i)
                AppState.set("bs_open", True)
                st.rerun()

    # ---- prev / next / play ----
    def _render_controls(self, stages) -> None:
        st.markdown("<div style='height:.4rem;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Prev", use_container_width=True, disabled=self._index() == 0):
                AppState.set("bs_index", self._index() - 1)
                AppState.set("bs_open", True)
                st.rerun()
        with c2:
            if st.button("Next", use_container_width=True,
                         disabled=self._index() == len(stages) - 1):
                AppState.set("bs_index", self._index() + 1)
                AppState.set("bs_open", True)
                st.rerun()
        with c3:
            if st.button("Play", type="primary", use_container_width=True):
                self._play(stages)

    def _play(self, stages) -> None:
        bar = st.progress(0.0, text="Booting...")
        for i in range(len(stages)):
            AppState.set("bs_index", i)
            bar.progress((i + 1) / len(stages), text=f"[{stages[i].order}] {stages[i].name}")
            time.sleep(0.6)
        st.rerun()

    # ---- flow diagram (highlights active stage) ----
    def _render_diagram(self, stages) -> None:
        active = self._index()
        nodes, edges = [], []
        for i, s in enumerate(stages):
            fill = _P.accent if i == active else _P.surface_alt
            font = "#ffffff" if i == active else _P.text
            nodes.append(
                f'"{i}" [label="{s.order}. {s.name}\\n{s.component}", '
                f'shape=box, style="rounded,filled", fillcolor="{fill}", '
                f'fontcolor="{font}", color="{_P.border}", fontname="Inter", fontsize=11];'
            )
            if i > 0:
                edges.append(f'"{i-1}" -> "{i}";')
        dot = (
            'digraph {rankdir=TB; bgcolor="transparent"; nodesep=0.25; ranksep=0.3; '
            'edge [color="#9aa4b0", arrowsize=0.7]; '
            + " ".join(nodes) + " " + " ".join(edges) + "}"
        )
        st.graphviz_chart(dot, use_container_width=True)

    # ---- detail content (reused by the modal) ----
    def _detail_html(self, stage: BootStage) -> str:
        files = "".join(f"<code>{f}</code> " for f in stage.key_files)
        return f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.5rem;">
                <span class="ps-pill">Phase {stage.order}</span>
                <span style="font-weight:700;font-size:1.1rem;">{stage.name}</span>
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">Component</div>
              <div style="margin-bottom:.5rem;">{stage.component}</div>
              <div class="ps-kv">What happens</div>
              <div style="margin-bottom:.5rem;">{stage.summary}</div>
              <div class="ps-kv">Key files / artifacts</div>
              <div style="margin-bottom:.5rem;">{files}</div>
              <div style="background:{_P.accent_soft};border-left:3px solid {_P.accent};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{_P.accent};">Security relevance</div>
                <div style="font-size:.9rem;">{stage.security_note}</div>
              </div>
            </div>
            """

    # ---- detail modal ----
    def _detail_dialog(self, stage: BootStage) -> None:
        @st.dialog(f"{stage.order}. {stage.name}", width="large")
        def _modal():
            st.markdown(self._detail_html(stage), unsafe_allow_html=True)
            if st.button("Close", key="bs_modal_close", use_container_width=True):
                st.rerun()
        _modal()

    # ---- guard against stale index after OS switch ----
    def _clamp_index(self, stages) -> None:
        if self._index() >= len(stages):
            AppState.set("bs_index", 0)
