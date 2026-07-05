"""Defense Simulator - Windows Incident Response & Blue Team training lab.

Left: Windows attack scenarios. Middle: the IR workflow timeline + interactive
investigation (inspect process, parent diagram, logs, registry, containment
decision with feedback). Right: detection, commands, artifacts, MITRE, notes.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.defense_simulator.defense_model import DefenseRepository, ScenarioModel

_P = AppConfig.PALETTE

WORKFLOW = ["Suspicious Activity", "Alert Generated", "Identify Process", "Analyze Parent Process",
            "Inspect Loaded Modules", "Check Registry", "Inspect Services", "Contain Threat",
            "Remove Persistence", "Restore System"]

SEV_BADGE = {"Critical": "critical", "High": "warning", "Medium": "neutral", "Low": "info"}
VERDICT_BADGE = {"Malicious": "critical", "Compromised": "critical",
                 "Suspicious": "warning", "Legitimate": "success"}
SUSPECT_KW = ("suspicious", "unsigned", "rwx", "unbacked", "hollowed", "beacon")

CHECKLIST = ["Verify the alert", "Identify the malicious process", "Check the parent process",
             "Inspect loaded DLLs", "Review Event Viewer logs", "Check startup locations",
             "Examine registry persistence", "Inspect scheduled tasks", "Review Windows services",
             "Isolate the affected system", "Terminate the malicious process", "Remove persistence",
             "Validate system integrity", "Monitor for recurrence"]


class DefenseSimulatorModule(BaseModule):
    def __init__(self) -> None:
        self._repo = DefenseRepository.from_json(JsonDataLoader(), "defense_scenarios.json")

    @property
    def id(self) -> str:
        return "defense_simulator"

    @property
    def title(self) -> str:
        return "Defense Simulator"

    @property
    def icon(self) -> str:
        return "\U0001f575"

    @property
    def description(self) -> str:
        return "Windows Incident Response lab - detect, investigate and remediate attacks on core OS components."

    # ---- entry point ----
    def render(self) -> None:
        scenarios = self._repo.all()
        st.session_state.setdefault("ds_scenario", scenarios[0].id)
        st.session_state.setdefault("ds_step", 0)
        page_header("Defense Simulator", self.description, pill="Blue Team")

        scen = self._repo.get(AppState.get("ds_scenario")) or scenarios[0]
        st.markdown(
            f'<div style="margin-bottom:.4rem;">Attacked component '
            f'{status_badge(scen.target, "info")} &nbsp; Severity '
            f'{status_badge(scen.severity, SEV_BADGE.get(scen.severity, "neutral"))}</div>',
            unsafe_allow_html=True)

        left, mid, right = st.columns([1, 1.7, 1.3], gap="large")
        with left:
            self._render_scenarios(scenarios)
        with mid:
            self._render_workflow(scen)
        with right:
            self._render_reference(scen)

    # ---- left: scenarios ----
    def _render_scenarios(self, scenarios) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Windows attack scenarios</div>',
                    unsafe_allow_html=True)
        for s in scenarios:
            active = s.id == AppState.get("ds_scenario")
            if st.button(s.name, key=f"ds_s_{s.id}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("ds_scenario", s.id)
                AppState.set("ds_step", 0)
                st.rerun()

    # ---- middle: workflow ----
    def _render_workflow(self, scen: ScenarioModel) -> None:
        cur = AppState.get("ds_step")
        if cur >= len(WORKFLOW):
            cur = 0; AppState.set("ds_step", 0)
        st.progress((cur + 1) / len(WORKFLOW), text=f"Stage {cur+1}/{len(WORKFLOW)}: {WORKFLOW[cur]}")

        html = ""
        for i, name in enumerate(WORKFLOW):
            cls = "ps-layer cur" if i == cur else ("ps-layer on" if i < cur else "ps-layer")
            html += f'<div class="{cls}"><span class="dot"></span>{name}</div>'
        st.markdown(html, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Prev stage", use_container_width=True, disabled=cur == 0):
                AppState.set("ds_step", cur - 1); st.rerun()
        with c2:
            if st.button("Next stage", use_container_width=True, disabled=cur == len(WORKFLOW) - 1):
                AppState.set("ds_step", cur + 1); st.rerun()

        self._render_stage(scen, cur)

        with st.expander("Defender checklist"):
            done = 0
            for i, item in enumerate(CHECKLIST):
                if st.checkbox(item, key=f"ds_chk_{scen.id}_{i}"):
                    done += 1
            st.progress(done / len(CHECKLIST), text=f"{done}/{len(CHECKLIST)} complete")

    def _render_stage(self, scen: ScenarioModel, cur: int) -> None:
        p = scen.process
        if cur == 0:
            self._card(scen.name, scen.summary)
            st.markdown(
                f'<div class="ps-card" style="border-left:3px solid {_P.success};">'
                f'<div class="ps-kv" style="color:{_P.success};">Expected (legitimate)</div>'
                f'<div>{scen.legit}</div></div>', unsafe_allow_html=True)
        elif cur == 1:
            self._card_list("How defenders were alerted", scen.detection["signals"])
            with st.expander("Simulated logs (Event Viewer / Sysmon)", expanded=True):
                for e in scen.event_logs:
                    st.markdown(f'`{e["src"]} {e["id"]}` &nbsp; {e["msg"]}')
        elif cur == 2:
            st.markdown(f'Suspicious process: **{p["name"]}** (PID {p["pid"]})')
            with st.expander("Inspect process details", expanded=True):
                st.markdown(
                    f'{status_badge(p.get("verdict","Suspicious"), VERDICT_BADGE.get(p.get("verdict"),"warning"))}'
                    f'&nbsp;&nbsp;Integrity: **{p.get("integrity","")}** &middot; User: `{p.get("user","")}`')
                st.markdown(f'- PID / PPID: `{p["pid"]}` / `{p.get("ppid","")}`')
                st.markdown(f'- Parent: `{p.get("parent","")}`')
                st.markdown(f'- Command line: `{p.get("cmdline","")}`')
                st.markdown(
                    f'<div style="background:rgba(239,68,68,.12);border-left:3px solid {_P.danger};'
                    f'border-radius:6px;padding:.5rem .7rem;margin-top:.4rem;">'
                    f'<div class="ps-kv" style="color:{_P.danger};">Why it is suspicious</div>'
                    f'<div>{p.get("why","")}</div></div>', unsafe_allow_html=True)
        elif cur == 3:
            self._parent_diagram(p)
            self._card("Parent-process analysis", scen.parent_note)
        elif cur == 4:
            st.markdown('<div class="ps-kv" style="margin:.3rem 0;">Loaded modules</div>',
                        unsafe_allow_html=True)
            for dll in p.get("dlls", []) or ["(none relevant)"]:
                mark = "  \u26a0" if any(k in dll.lower() for k in SUSPECT_KW) else ""
                st.markdown(f'- `{dll}`{mark}')
            if p.get("connections"):
                st.markdown('<div class="ps-kv" style="margin:.4rem 0;">Network connections</div>',
                            unsafe_allow_html=True)
                for c in p["connections"]:
                    st.markdown(f'- `{c}`')
            self._card("Analyst note", scen.modules_note)
        elif cur == 5:
            if scen.registry:
                self._card_list("Registry persistence found", [f"`{r}`" for r in scen.registry])
            else:
                st.info(f"No registry persistence in this scenario - focus on {scen.target}.")
        elif cur == 6:
            if scen.services:
                self._card_list("Related services", [f"`{s}`" for s in scen.services])
            else:
                st.info(f"No malicious service artifacts here - the focus is {scen.target}.")
        elif cur == 7:
            self._render_containment(scen)
        elif cur == 8:
            st.markdown('<div class="ps-kv" style="margin:.3rem 0;">Remove persistence - select the steps you would take</div>',
                        unsafe_allow_html=True)
            for i, step in enumerate(scen.eradication):
                st.checkbox(step, key=f"ds_erad_{scen.id}_{i}")
        elif cur == 9:
            self._card_list("Restore & validate", scen.recovery)
            st.success("Validate system integrity and confirm the threat does not recur before closing the incident.")

    def _render_containment(self, scen: ScenarioModel) -> None:
        c = scen.containment
        if not c:
            st.info("No containment decision for this scenario.")
            return
        st.markdown(f'**{c["q"]}**')
        choice = st.radio("Choose an action", [o["text"] for o in c["options"]],
                          key=f"ds_ct_{scen.id}", index=None, label_visibility="collapsed")
        if choice is not None:
            opt = next(o for o in c["options"] if o["text"] == choice)
            if opt["correct"]:
                st.success("Correct. " + opt["feedback"])
            else:
                st.error("Not ideal. " + opt["feedback"])

    # ---- right: reference ----
    def _render_reference(self, scen: ScenarioModel) -> None:
        t1, t2, t3, t4, t5, t6 = st.tabs(
            ["Detection", "Commands", "Artifacts", "MITRE", "Best Practices", "Notes"])
        with t1:
            st.markdown("**Detection tools**")
            for tool in scen.detection.get("tools", []):
                st.markdown(f"- {tool}")
            st.markdown("**Signals**")
            for sig in scen.detection.get("signals", []):
                st.markdown(f"- {sig}")
        with t2:
            for platform, cmds in scen.commands.items():
                st.markdown(f"**{platform}**")
                st.code("\n".join(cmds))
        with t3:
            for art in scen.artifacts:
                st.markdown(f"- {art}")
        with t4:
            for m in scen.mitre:
                st.markdown(f'{status_badge(m["tactic"], "info")} &nbsp; {m["technique"]}',
                            unsafe_allow_html=True)
        with t5:
            for bp in scen.best_practices:
                st.markdown(f"- {bp}")
        with t6:
            for n in scen.notes:
                st.markdown(f"- {n}")

    # ---- helpers ----
    def _card(self, title: str, body: str) -> None:
        st.markdown(f'<div class="ps-card"><div class="ps-kv">{title}</div>'
                    f'<div style="margin-top:.2rem;">{body}</div></div>', unsafe_allow_html=True)

    def _card_list(self, title: str, items) -> None:
        body = "".join(f'<li style="margin:.15rem 0;">{x}</li>' for x in items)
        st.markdown(f'<div class="ps-card"><div class="ps-kv">{title}</div>'
                    f'<ul style="margin:.3rem 0 0 1rem;padding:0;">{body}</ul></div>',
                    unsafe_allow_html=True)

    def _parent_diagram(self, p: dict) -> None:
        parent = p.get("parent", "parent")
        dot = (
            'digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.3; ranksep=0.7; '
            'edge [color="#9aa4b0", arrowsize=0.6]; '
            f'"par" [label="{parent}\\nPPID {p.get("ppid","")}", shape=box, style="rounded,filled", '
            f'fillcolor="{_P.surface_alt}", fontcolor="{_P.text}", color="{_P.border}", fontname="Inter", fontsize=10]; '
            f'"proc" [label="{p["name"]}\\nPID {p["pid"]}", shape=box, style="rounded,filled", '
            f'fillcolor="{_P.danger}", fontcolor="#ffffff", color="{_P.border}", fontname="Inter", fontsize=10]; '
            '"par" -> "proc"; }')
        st.graphviz_chart(dot, use_container_width=True)
