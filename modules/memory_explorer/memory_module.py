"""Module 6 - Memory Visualization.

Maps a process's virtual address space by size and protection, contrasting a
benign process with a hollowed one to teach the memory basis of injection.
"""
import streamlit as st
import plotly.graph_objects as go

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.memory_explorer.memory_model import MemoryRepository, MemoryRegion

_P = AppConfig.PALETTE

PROT_COLORS = {"RWX": _P.danger, "R-X": _P.accent, "RW-": _P.success, "R--": _P.info, "---": _P.text_muted}
PROT_BADGE = {"RWX": "critical", "R-X": "info", "RW-": "success", "R--": "neutral", "---": "neutral"}


class MemoryExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = MemoryRepository.from_json(JsonDataLoader(), "memory_maps.json")

    @property
    def id(self) -> str:
        return "memory_explorer"

    @property
    def title(self) -> str:
        return "Memory Explorer"

    @property
    def icon(self) -> str:
        return "\U0001f4be"

    @property
    def description(self) -> str:
        return "Map a process's virtual address space - regions, protections and injection signals."

    # ---- entry point ----
    def render(self) -> None:
        procs = self._repo.processes()
        st.session_state.setdefault("mem_proc", procs[0].key)
        page_header("Memory Explorer", self.description, pill="Module 6")

        self._render_proc_switch(procs)
        model = self._repo.get(AppState.get("mem_proc")) or procs[0]
        regions = model.regions

        bases = [r.base_hex for r in regions]
        if AppState.get("mem_selected") not in bases:
            AppState.set("mem_selected", bases[0])

        self._render_metrics(regions)

        left, right = st.columns([1, 1.6], gap="large")
        with left:
            self._render_list(regions)
        with right:
            self._render_map(regions)
            sel = next((r for r in regions if r.base_hex == AppState.get("mem_selected")), regions[0])
            self._render_detail(sel)

    # ---- process toggle ----
    def _render_proc_switch(self, procs) -> None:
        cols = st.columns(len(procs) + 2)
        for col, proc in zip(cols, procs):
            with col:
                active = proc.key == AppState.get("mem_proc")
                if st.button(proc.label, key=f"mem_p_{proc.key}",
                             type="primary" if active else "secondary",
                             use_container_width=True):
                    AppState.set("mem_proc", proc.key)
                    AppState.set("mem_selected", None)
                    st.rerun()

    # ---- metrics ----
    def _render_metrics(self, regions) -> None:
        total = len(regions)
        committed = sum(r.size for r in regions if r.state == "Committed")
        rwx = sum(1 for r in regions if r.protection == "RWX")
        metric_cards([
            ("Regions", str(total), _P.accent),
            ("Committed", self._hsize(committed), _P.info),
            ("RWX regions", str(rwx), _P.danger),
        ])

    # ---- region list ----
    def _render_list(self, regions) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Regions (low to high)</div>',
                    unsafe_allow_html=True)
        for r in sorted(regions, key=lambda x: x.base):
            mark = "  \u26a0" if r.suspicious else ""
            active = r.base_hex == AppState.get("mem_selected")
            if st.button(f"{r.base_hex}  \u00b7  {r.region_type}{mark}",
                         key=f"mem_r_{r.base_hex}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("mem_selected", r.base_hex)
                st.rerun()

    # ---- address-space map (Plotly) ----
    def _render_map(self, regions) -> None:
        legend = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:.8rem;'
            f'font-size:.75rem;color:{_P.text_muted};">'
            f'<span style="width:10px;height:10px;border-radius:3px;background:{col};'
            f'display:inline-block;"></span>{prot}</span>'
            for prot, col in PROT_COLORS.items()
        )
        st.markdown(f'<div style="margin:.1rem 0 .4rem;">{legend}</div>', unsafe_allow_html=True)

        regs = sorted(regions, key=lambda r: r.base)
        sel = AppState.get("mem_selected")
        labels = [f"{r.base_hex}  {r.detail}" for r in regs]
        sizes = [r.size for r in regs]
        colors = [PROT_COLORS.get(r.protection, _P.text_muted) for r in regs]
        line_w = [3 if r.base_hex == sel else 0 for r in regs]
        line_c = [_P.text if r.base_hex == sel else "rgba(0,0,0,0)" for r in regs]
        hover = [f"{r.base_hex} &middot; {r.region_type}<br>Prot {r.protection} &middot; {r.state}"
                 f"<br>Size {self._hsize(r.size)}" for r in regs]

        fig = go.Figure(go.Bar(
            x=sizes, y=labels, orientation="h",
            marker=dict(color=colors, line=dict(color=line_c, width=line_w)),
            hovertext=hover, hoverinfo="text",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=_P.text, size=11), showlegend=False,
            height=max(300, len(regs) * 42), margin=dict(l=10, r=10, t=6, b=34), bargap=0.35,
        )
        fig.update_xaxes(type="log", title="Region size (bytes, log scale)",
                         gridcolor=_P.border, zeroline=False)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)", automargin=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---- detail panel ----
    def _render_detail(self, r: MemoryRegion) -> None:
        badges = (
            status_badge(r.protection, PROT_BADGE.get(r.protection, "neutral")) + " "
            + status_badge(r.state, "success" if r.state == "Committed" else "neutral")
        )
        if r.suspicious:
            badges += " " + status_badge("Suspicious", "critical")
        box_color = _P.danger if r.suspicious else _P.accent
        box_bg = "rgba(239,68,68,.12)" if r.suspicious else _P.accent_soft
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.1rem;">{r.detail}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">Base address</div>
              <div style="margin-bottom:.5rem;"><code>{r.base_hex}</code></div>
              <div class="ps-kv">Region type / Size</div>
              <div style="margin-bottom:.5rem;">{r.region_type} &nbsp;&middot;&nbsp; {self._hsize(r.size)}</div>
              <div class="ps-kv">Protection / State</div>
              <div style="margin-bottom:.5rem;">{r.protection} &nbsp;&middot;&nbsp; {r.state}</div>
              <div style="background:{box_bg};border-left:3px solid {box_color};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.4rem;">
                <div class="ps-kv" style="color:{box_color};">Analysis</div>
                <div style="font-size:.9rem;">{r.note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- helpers ----
    @staticmethod
    def _hsize(n) -> str:
        size = float(n)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.0f} TB"
