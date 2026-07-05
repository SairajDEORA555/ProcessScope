"""Module 12 - SOC Investigation Workspace.

Correlates all TelemetryStore alerts into a single incident: unified timeline,
reconstructed attack story, MITRE coverage, consolidated IOCs, business impact,
an interactive containment/recovery checklist, and a .docx report export.
"""
import re
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.telemetry import TelemetryStore

try:
    from modules.soc_workspace.report_builder import build_docx
    _DOCX_OK = True
except Exception:
    _DOCX_OK = False

_P = AppConfig.PALETTE

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2}
SEV_BADGE = {"Critical": "critical", "High": "warning", "Medium": "neutral"}
SEV_COLOR = {"Critical": _P.danger, "High": _P.warning, "Medium": _P.text_muted}

PHASE_ORDER = {
    "Initial Access": 1, "Execution": 2, "Persistence": 3, "Privilege Escalation": 4,
    "Defense Evasion": 5, "Credential Access": 6, "Discovery": 7, "Lateral Movement": 8,
    "Command and Control": 9, "Exfiltration": 10, "Impact": 11,
}

IMPACT_BY_TACTIC = {
    "Impact": "Data destruction / ransomware - direct business disruption, potential downtime and data loss.",
    "Credential Access": "Credential compromise - risk of account takeover and lateral movement across the estate.",
    "Exfiltration": "Data exfiltration - possible data breach with regulatory and reputational exposure.",
    "Command and Control": "Active attacker control of the host - ongoing hands-on-keyboard risk.",
    "Persistence": "Attacker maintains a foothold that survives reboots.",
    "Defense Evasion": "Evasion techniques in use - detection gaps and possible tampering with security tooling.",
    "Execution": "Arbitrary code execution achieved on the endpoint.",
}


class SOCWorkspaceModule(BaseModule):
    @property
    def id(self) -> str:
        return "soc_workspace"

    @property
    def title(self) -> str:
        return "SOC Workspace"

    @property
    def icon(self) -> str:
        return "\U0001f50e"

    @property
    def description(self) -> str:
        return "Correlate all detections into one incident - timeline, story, impact and recovery."

    # ---- entry point ----
    def render(self) -> None:
        page_header("SOC Investigation Workspace", self.description, pill="Module 12")

        alerts = sorted(TelemetryStore.alerts(),
                        key=lambda a: (SEV_ORDER.get(a["severity"], 9), a["time"]))
        if not alerts:
            st.info("No incident to investigate yet. Run attacks in the **Attack Simulator** "
                    "(Module 10) to generate telemetry, then return here.")
            return

        self._render_summary(alerts)
        self._render_metrics(alerts)

        tabs = st.tabs(["Timeline", "Attack Story", "MITRE ATT&CK", "IOCs",
                        "Impact", "Containment & Recovery", "Report"])
        with tabs[0]:
            self._timeline()
        with tabs[1]:
            self._story(alerts)
        with tabs[2]:
            self._mitre(alerts)
        with tabs[3]:
            self._iocs(alerts)
        with tabs[4]:
            self._impact(alerts)
        with tabs[5]:
            self._recovery()
        with tabs[6]:
            self._report()

    # ---- incident summary ----
    def _render_summary(self, alerts) -> None:
        severity = min((a["severity"] for a in alerts), key=lambda s: SEV_ORDER.get(s, 9))
        times = [e["time"] for e in TelemetryStore.events()] or [a["time"] for a in alerts]
        span = f"{min(times)} - {max(times)}" if times else "-"
        inc_id = f"INC-2026-{7000 + len(alerts)}"
        isolated = AppState.get("edr_isolated", False)
        status = ("Contained", "success") if isolated else ("Active", "critical")
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;">
                <span style="font-weight:800;font-size:1.15rem;">{inc_id}</span>
                {status_badge(severity, SEV_BADGE.get(severity, "neutral"))}
                {status_badge(status[0], status[1])}
                <span class="ps-kv" style="margin-left:auto;">Window {span}</span>
              </div>
              <div style="margin-top:.4rem;color:{_P.text_muted};">
                {len(alerts)} correlated detections on host <strong style="color:{_P.text};">DESKTOP-PS</strong>
                (user Manas). Multi-stage intrusion spanning
                {len({a["tactic"] for a in alerts})} ATT&amp;CK tactics.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- metrics ----
    def _render_metrics(self, alerts) -> None:
        techniques = {a["technique"] for a in alerts}
        iocs = {i for a in alerts for i in a.get("iocs", [])}
        metric_cards([
            ("Detections", str(len(alerts)), _P.accent),
            ("Techniques", str(len(techniques)), _P.info),
            ("IOCs", str(len(iocs)), _P.warning),
            ("Events", str(len(TelemetryStore.events())), _P.danger),
        ])

    # ---- timeline ----
    def _timeline(self) -> None:
        events = sorted(TelemetryStore.events(), key=lambda e: e["time"])
        for e in events:
            color = SEV_COLOR.get(e["severity"], _P.text_muted)
            st.markdown(
                f'<div style="display:flex;gap:.6rem;align-items:flex-start;padding:.35rem 0;'
                f'border-bottom:1px solid {_P.surface_alt};">'
                f'<span style="width:8px;height:8px;border-radius:50%;background:{color};'
                f'margin-top:.4rem;flex:none;"></span>'
                f'<div><code>{e["time"]}</code> &nbsp; <strong>{e["source"]} {e["event_id"]}</strong>'
                f' &nbsp;<span class="ps-kv">{e["attack"]}</span><br>'
                f'<span style="font-size:.9rem;">{e["message"]}</span></div></div>',
                unsafe_allow_html=True,
            )

    # ---- attack story ----
    def _story(self, alerts) -> None:
        ordered = sorted(alerts, key=lambda a: PHASE_ORDER.get(a["tactic"], 99))
        nodes, edges, prev = [], [], None
        for a in ordered:
            color = SEV_COLOR.get(a["severity"], _P.surface_alt)
            nodes.append(
                f'"{a["id"]}" [label="{a["tactic"]}\\n{a["name"]}", shape=box, '
                f'style="rounded,filled", fillcolor="{color}", fontcolor="#ffffff", '
                f'color="{_P.border}", fontname="Inter", fontsize=10];'
            )
            if prev:
                edges.append(f'"{prev}" -> "{a["id"]}";')
            prev = a["id"]
        dot = ('digraph {rankdir=LR; bgcolor="transparent"; nodesep=0.25; ranksep=0.55; '
               'edge [color="#9aa4b0", arrowsize=0.6]; '
               + " ".join(nodes) + " " + " ".join(edges) + "}")
        st.graphviz_chart(dot, use_container_width=True)
        for i, a in enumerate(ordered, 1):
            st.markdown(f'**{i}. {a["tactic"]} - {a["name"]}** &nbsp;`{a["technique"]}`  \n'
                        f'{a["description"]}')

    # ---- MITRE coverage ----
    def _mitre(self, alerts) -> None:
        by_tactic = {}
        for a in alerts:
            by_tactic.setdefault(a["tactic"], []).append(a)
        for tactic in sorted(by_tactic, key=lambda t: PHASE_ORDER.get(t, 99)):
            techs = "".join(
                f'<div style="margin:.2rem 0;">{status_badge(a["technique"], "info")} '
                f'<span style="color:{_P.text};">{a["name"]}</span></div>'
                for a in by_tactic[tactic]
            )
            st.markdown(
                f'<div class="ps-card"><div style="font-weight:700;margin-bottom:.3rem;">{tactic}</div>'
                f'{techs}</div>',
                unsafe_allow_html=True,
            )

    # ---- consolidated IOCs ----
    def _iocs(self, alerts) -> None:
        ioc_map = {}
        for a in alerts:
            for ioc in a.get("iocs", []):
                ioc_map.setdefault(ioc, set()).add(a["name"])
        for ioc in sorted(ioc_map):
            kind, badge = self._ioc_type(ioc)
            sources = ", ".join(sorted(ioc_map[ioc]))
            st.markdown(
                f'<div style="padding:.35rem 0;border-bottom:1px solid {_P.surface_alt};">'
                f'{status_badge(kind, badge)} &nbsp;<code>{ioc}</code>'
                f'<div class="ps-kv" style="margin-top:.15rem;">from: {sources}</div></div>',
                unsafe_allow_html=True,
            )

    @staticmethod
    def _ioc_type(ioc: str):
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}", ioc):
            return "IP", "critical"
        if ".com" in ioc or "http" in ioc or "attacker" in ioc:
            return "Domain/URL", "warning"
        if any(x in ioc.lower() for x in [".exe", ".dll", ".dmp", "\\", ".locked", ".txt"]):
            return "Host/File", "info"
        return "Behavioral", "neutral"

    # ---- business impact ----
    def _impact(self, alerts) -> None:
        tactics = {a["tactic"] for a in alerts}
        severity = min((a["severity"] for a in alerts), key=lambda s: SEV_ORDER.get(s, 9))
        rating = {"Critical": ("Critical", _P.danger), "High": ("High", _P.warning),
                  "Medium": ("Moderate", _P.text_muted)}.get(severity, ("Moderate", _P.text_muted))
        st.markdown(
            f'<div class="ps-card" style="border-left:3px solid {rating[1]};">'
            f'<div class="ps-kv">Overall business impact</div>'
            f'<div style="font-size:1.3rem;font-weight:800;color:{rating[1]};">{rating[0]}</div></div>',
            unsafe_allow_html=True,
        )
        for tactic in sorted(tactics, key=lambda t: PHASE_ORDER.get(t, 99)):
            if tactic in IMPACT_BY_TACTIC:
                st.markdown(f'- **{tactic}:** {IMPACT_BY_TACTIC[tactic]}')

        st.markdown('<div class="ps-kv" style="margin-top:.7rem;">Affected assets</div>',
                    unsafe_allow_html=True)
        procs = sorted({p["name"] for p in TelemetryStore.processes()})
        ips = sorted({c["remote"] for c in TelemetryStore.connections()})
        st.markdown('- **Host:** DESKTOP-PS (user Manas)')
        if procs:
            st.markdown(f'- **Processes:** {", ".join(procs)}')
        if ips:
            st.markdown(f'- **Remote endpoints:** {", ".join(ips)}')

    # ---- containment & recovery ----
    def _recovery(self) -> None:
        containment = [
            "Isolate affected host(s) from the network",
            "Terminate malicious processes",
            "Block C2 IPs / domains at the perimeter",
            "Disable and rotate compromised credentials",
            "Remove persistence mechanisms",
        ]
        recovery = [
            "Preserve forensic evidence (memory + disk image)",
            "Validate offline backups are intact",
            "Rebuild or restore affected systems",
            "Reset exposed secrets, tokens and Kerberos krbtgt",
            "Apply hardening and monitor for recurrence",
        ]
        self._checklist("Containment", containment, "soc_cont")
        self._checklist("Recovery", recovery, "soc_rec")

    def _checklist(self, title: str, items, prefix: str) -> None:
        st.markdown(f'<div class="ps-kv" style="margin:.5rem 0 .3rem;">{title}</div>',
                    unsafe_allow_html=True)
        done = 0
        for i, item in enumerate(items):
            if st.checkbox(item, key=f"{prefix}_{i}"):
                done += 1
        st.progress(done / len(items), text=f"{done}/{len(items)} complete")

    # ---- report export ----
    def _report(self) -> None:
        st.markdown("Generate a formatted Word incident report from the current telemetry.")
        if not _DOCX_OK:
            st.warning("Report export needs python-docx. Install it and restart:\n\n"
                       "`python -m pip install python-docx`")
            return
        data = build_docx()
        st.download_button(
            "Download incident report (.docx)",
            data=data,
            file_name="ProcessScope_Incident_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
