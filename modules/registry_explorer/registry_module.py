"""Module 5 - Registry & Configuration Explorer.

Navigate the Windows registry as a hive tree down to key/value level, with a
focus on the persistence and configuration keys defenders investigate.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge, metric_cards
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.registry_explorer.registry_model import RegistryRepository, RegistryNode

_P = AppConfig.PALETTE

_DEFAULT = "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"


class RegistryExplorerModule(BaseModule):
    def __init__(self) -> None:
        self._repo = RegistryRepository.from_json(JsonDataLoader(), "registry_windows.json")

    @property
    def id(self) -> str:
        return "registry_explorer"

    @property
    def title(self) -> str:
        return "Registry Explorer"

    @property
    def icon(self) -> str:
        return "\U0001f5c4"

    @property
    def description(self) -> str:
        return "Navigate the registry hive tree and the keys attackers use for persistence."

    # ---- entry point ----
    def render(self) -> None:
        st.session_state.setdefault("re_selected", _DEFAULT)
        page_header("Registry Explorer", self.description, pill="Module 5")

        self._render_metrics()

        c1, c2 = st.columns([1, 2])
        with c1:
            category = st.selectbox("Category", ["All"] + self._repo.categories(), key="re_cat")
        with c2:
            query = st.text_input("Search keys",
                                  placeholder="Path, value name, or MITRE technique...",
                                  key="re_query").strip()

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            if query or category != "All":
                self._render_flat(query, category)
            else:
                self._render_tree()
        with right:
            node = self._repo.get_node(AppState.get("re_selected"))
            self._render_detail(node)

    # ---- metrics ----
    def _render_metrics(self) -> None:
        keys = self._repo.all_keys()
        total = len(keys)
        persist = sum(1 for k in keys if k.persistence)
        values = sum(len(k.values) for k in keys)
        metric_cards([
            ("Keys", str(total), _P.accent),
            ("Persistence keys", str(persist), _P.danger),
            ("Values", str(values), _P.info),
        ])

    # ---- tree ----
    def _render_tree(self) -> None:
        st.markdown('<div class="ps-kv" style="margin:.4rem 0 .5rem;">Registry Hives</div>',
                    unsafe_allow_html=True)
        for root in self._repo.roots():
            self._render_node(root, 0)

    def _render_node(self, node: RegistryNode, depth: int) -> None:
        label = f"{self._prefix(depth)}{node.name}"
        if node.model is not None and node.model.persistence:
            label += "  \u26a0"
        active = node.path == AppState.get("re_selected")
        if st.button(label, key=f"re_{node.path}",
                     type="primary" if active else "secondary",
                     use_container_width=True):
            AppState.set("re_selected", node.path)
            st.rerun()
        for child in sorted(node.children.values(), key=lambda n: n.name):
            self._render_node(child, depth + 1)

    @staticmethod
    def _prefix(depth: int) -> str:
        if depth == 0:
            return ""
        return "\u2502  " * (depth - 1) + "\u2514\u2500 "

    # ---- flat (search / filter) ----
    def _render_flat(self, query: str, category: str) -> None:
        q = query.lower()

        def matches(k) -> bool:
            if category != "All" and k.category != category:
                return False
            if q:
                hay = " ".join([
                    k.path.lower(), k.description.lower(), k.mitre.lower(),
                    " ".join(f'{v["name"]} {v["data"]}'.lower() for v in k.values),
                ])
                if q not in hay:
                    return False
            return True

        results = [k for k in self._repo.all_keys() if matches(k)]
        st.markdown(f'<div class="ps-kv" style="margin:.4rem 0 .5rem;">'
                    f'{len(results)} key(s)</div>', unsafe_allow_html=True)
        for k in results:
            leaf = k.path.split("\\")[-1]
            active = k.path == AppState.get("re_selected")
            mark = "  \u26a0" if k.persistence else ""
            if st.button(f"{leaf}{mark}", key=f"re_flat_{k.path}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("re_selected", k.path)
                st.rerun()
        if not results:
            st.caption("No keys match your filters.")

    # ---- values table ----
    def _values_table(self, values) -> str:
        if not values:
            return f'<div style="color:{_P.text_muted};font-size:.85rem;">(No values defined)</div>'
        head = (
            '<tr>'
            f'<th style="text-align:left;padding:.3rem .5rem;color:{_P.text_muted};'
            f'font-weight:600;border-bottom:1px solid {_P.border};">Name</th>'
            f'<th style="text-align:left;padding:.3rem .5rem;color:{_P.text_muted};'
            f'font-weight:600;border-bottom:1px solid {_P.border};">Type</th>'
            f'<th style="text-align:left;padding:.3rem .5rem;color:{_P.text_muted};'
            f'font-weight:600;border-bottom:1px solid {_P.border};">Data</th>'
            '</tr>'
        )
        body = ""
        for v in values:
            body += (
                '<tr>'
                f'<td style="padding:.3rem .5rem;border-bottom:1px solid {_P.surface_alt};">{v["name"]}</td>'
                f'<td style="padding:.3rem .5rem;border-bottom:1px solid {_P.surface_alt};"><code>{v["type"]}</code></td>'
                f'<td style="padding:.3rem .5rem;border-bottom:1px solid {_P.surface_alt};word-break:break-all;">{v["data"]}</td>'
                '</tr>'
            )
        return f'<table style="width:100%;border-collapse:collapse;font-size:.82rem;">{head}{body}</table>'

    # ---- detail panel ----
    def _render_detail(self, node) -> None:
        if node is None:
            st.info("Select a registry key to see its details.")
            return

        if node.model is None:
            child_count = len(node.children)
            st.markdown(
                f"""
                <div class="ps-card">
                  <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                    <span style="font-weight:700;font-size:1.05rem;">{node.name}</span>
                    {status_badge("Container key", "neutral")}
                  </div>
                  <div class="ps-kv" style="margin-top:.7rem;">Full path</div>
                  <div style="margin-bottom:.5rem;"><code>{node.path}</code></div>
                  <div class="ps-kv">Subkeys</div>
                  <div>{child_count} child key(s). Expand this branch in the tree to drill down.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        m = node.model
        badges = (
            (status_badge("Persistence", "critical") if m.persistence
             else status_badge("Config key", "neutral"))
            + " " + status_badge(m.category, "info")
        )
        mitre_html = (f'<div class="ps-kv">MITRE ATT&amp;CK</div>'
                      f'<div style="margin-bottom:.5rem;">{m.mitre}</div>') if m.mitre else ""
        st.markdown(
            f"""
            <div class="ps-card">
              <div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:1.05rem;">{node.name}</span>
                {badges}
              </div>
              <div class="ps-kv" style="margin-top:.7rem;">Full path</div>
              <div style="margin-bottom:.5rem;"><code>{m.path}</code></div>
              <div class="ps-kv">Purpose</div>
              <div style="margin-bottom:.5rem;">{m.description}</div>
              {mitre_html}
              <div class="ps-kv">Values</div>
              <div style="margin:.2rem 0 .6rem;">{self._values_table(m.values)}</div>
              <div style="background:{_P.accent_soft};border-left:3px solid {_P.accent};
                   border-radius:6px;padding:.6rem .8rem;margin-top:.2rem;">
                <div class="ps-kv" style="color:{_P.accent};">Security relevance</div>
                <div style="font-size:.9rem;">{m.security_note}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
