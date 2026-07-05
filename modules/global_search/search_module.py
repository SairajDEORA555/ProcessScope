"""Module 14 - Global Search.

Indexes every dataset (processes, services, drivers, registry, connections,
attacks) and navigates directly to the owning module on click.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader

_P = AppConfig.PALETTE

TYPE_BADGE = {
    "Process": "info", "Service": "success", "Driver": "warning",
    "Registry": "neutral", "Connection": "info", "Attack": "critical",
}


class GlobalSearchModule(BaseModule):
    def __init__(self) -> None:
        self._index = self._build_index()

    @property
    def id(self) -> str:
        return "global_search"

    @property
    def title(self) -> str:
        return "Global Search"

    @property
    def icon(self) -> str:
        return "\U0001f50d"

    @property
    def description(self) -> str:
        return "Search processes, services, drivers, registry keys, ports and techniques."

    # ---- index ----
    def _build_index(self):
        loader = JsonDataLoader()
        recs = []
        for p in loader.load("processes_windows.json"):
            recs.append({"type": "Process", "title": p["name"],
                         "sub": f"PID {p['pid']} - {p['integrity']}",
                         "module": "process_explorer", "key": "pe_selected_pid", "value": p["pid"],
                         "hay": f"{p['name']} {p['pid']} {p['command_line']} {p['user']}".lower()})
        for s in loader.load("services_windows.json"):
            recs.append({"type": "Service", "title": s["display_name"], "sub": s["name"],
                         "module": "service_explorer", "key": "se_selected", "value": s["name"],
                         "hay": f"{s['name']} {s['display_name']} {s['description']}".lower()})
        for d in loader.load("drivers_windows.json"):
            recs.append({"type": "Driver", "title": d["display_name"],
                         "sub": f"{d['name']} - {d['signer']}",
                         "module": "driver_explorer", "key": "de_selected", "value": d["name"],
                         "hay": f"{d['name']} {d['display_name']} {d['signer']} {d['hardware']}".lower()})
        for r in loader.load("registry_windows.json"):
            recs.append({"type": "Registry", "title": r["path"].split("\\")[-1], "sub": r["path"],
                         "module": "registry_explorer", "key": "re_selected", "value": r["path"],
                         "hay": f"{r['path']} {r.get('description','')} {r.get('mitre','')}".lower()})
        for i, c in enumerate(loader.load("connections.json")):
            ep = f":{c['local_port']}" if c["state"] == "LISTENING" else f"{c['remote_addr']}:{c['remote_port']}"
            recs.append({"type": "Connection", "title": ep, "sub": f"{c['process']} - {c['service']}",
                         "module": "network_explorer", "key": "net_selected", "value": i,
                         "hay": f"{c['process']} {c['remote_addr']} {c['remote_port']} {c['local_port']} {c['service']}".lower()})
        for a in loader.load("attacks.json"):
            recs.append({"type": "Attack", "title": a["name"], "sub": f"{a['technique']} - {a['tactic']}",
                         "module": "attack_simulator", "key": "atk_selected", "value": a["id"],
                         "hay": f"{a['name']} {a['technique']} {a['tactic']} {' '.join(a.get('iocs', []))}".lower()})
        return recs

    # ---- entry point ----
    def render(self) -> None:
        page_header("Global Search", self.description, pill="Module 14")
        query = st.text_input("Search everything",
                              placeholder="e.g. lsass, 4444, T1558, Spooler, HKLM Run...",
                              key="gs_query").strip().lower()

        if not query:
            counts = {}
            for r in self._index:
                counts[r["type"]] = counts.get(r["type"], 0) + 1
            metric_cards([("Indexed items", str(len(self._index)), _P.accent),
                          ("Categories", str(len(counts)), _P.info),
                          ("Attacks", str(counts.get("Attack", 0)), _P.danger)])
            st.caption("Type a process name, PID, port, service, registry key or MITRE technique. "
                       "Click a result to jump to its module.")
            return

        matches = [r for r in self._index if query in r["hay"]]
        st.markdown(f'<div class="ps-kv" style="margin:.4rem 0 .5rem;">'
                    f'{len(matches)} result(s)</div>', unsafe_allow_html=True)

        by_type = {}
        for r in matches:
            by_type.setdefault(r["type"], []).append(r)

        for rtype in sorted(by_type):
            st.markdown(f'<div style="margin-top:.4rem;">{status_badge(rtype, TYPE_BADGE.get(rtype, "neutral"))}'
                        f' <span class="ps-kv">{len(by_type[rtype])}</span></div>', unsafe_allow_html=True)
            for r in by_type[rtype]:
                if st.button(f"{r['title']}  \u00b7  {r['sub']}",
                             key=f"gs_{r['module']}_{r['value']}",
                             use_container_width=True):
                    AppState.set(r["key"], r["value"])
                    AppState.set("active_module", r["module"])
                    st.rerun()

        if not matches:
            st.caption("No results. Try a process name, port, service, registry path or technique ID.")
