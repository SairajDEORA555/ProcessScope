"""Module 13 - Learning Center.

A searchable reference of OS and security topics, each rendered through a fixed
template: purpose, architecture, logs, attacks, detection, Sigma/YARA, hardening.
"""
import streamlit as st

from modules.base_module import BaseModule
from components.ui import page_header, status_badge
from core.config import AppConfig
from core.state import AppState
from core.data_loader import JsonDataLoader
from modules.learning_center.learning_model import LearningRepository, LearningTopic

_P = AppConfig.PALETTE

SECTIONS = [
    ("purpose", "Purpose"),
    ("architecture", "Architecture / How it works"),
    ("dependencies", "Dependencies"),
    ("windows_logs", "Windows logs & Event IDs"),
    ("linux_logs", "Linux logs"),
    ("sysmon", "Sysmon events"),
    ("common_attacks", "Common attacks"),
    ("detection", "Detection methods"),
    ("sigma", "Sigma rule"),
    ("yara", "YARA rule"),
    ("hardening", "Hardening"),
    ("enterprise", "Enterprise use cases"),
]


class LearningCenterModule(BaseModule):
    def __init__(self) -> None:
        self._repo = LearningRepository.from_json(JsonDataLoader(), "learning.json")

    @property
    def id(self) -> str:
        return "learning_center"

    @property
    def title(self) -> str:
        return "Learning Center"

    @property
    def icon(self) -> str:
        return "\U0001f4d8"

    @property
    def description(self) -> str:
        return "Reference cards for every OS component - logs, attacks, detection and hardening."

    def render(self) -> None:
        topics = self._repo.all()
        st.session_state.setdefault("lc_selected", topics[0].id)
        page_header("Learning Center", self.description, pill="Module 13")

        c1, c2 = st.columns([1, 2])
        with c1:
            category = st.selectbox("Category", ["All"] + self._repo.categories(), key="lc_cat")
        with c2:
            query = st.text_input("Search topics", placeholder="Keyword, Event ID, technique...",
                                  key="lc_query").strip().lower()

        left, right = st.columns([1, 2], gap="large")
        with left:
            self._render_list(category, query)
        with right:
            topic = self._repo.get(AppState.get("lc_selected"))
            if topic is None:
                st.info("Select a topic.")
            else:
                self._render_topic(topic)

    def _render_list(self, category: str, query: str) -> None:
        topics = self._repo.all()
        if category != "All":
            topics = [t for t in topics if t.category == category]
        if query:
            topics = [t for t in topics if query in t.haystack()]
        st.markdown(f'<div class="ps-kv" style="margin:.2rem 0 .5rem;">'
                    f'{len(topics)} topic(s)</div>', unsafe_allow_html=True)
        for t in topics:
            active = t.id == AppState.get("lc_selected")
            if st.button(t.title, key=f"lc_{t.id}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                AppState.set("lc_selected", t.id)
                st.rerun()
        if not topics:
            st.caption("No topics match your search.")

    def _render_topic(self, t: LearningTopic) -> None:
        st.markdown(
            f'<div class="ps-card">'
            f'<div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;">'
            f'<span style="font-weight:700;font-size:1.3rem;">{t.title}</span>'
            f'{status_badge(t.category, "info")}</div>'
            f'<div style="margin-top:.4rem;color:{_P.text};">{t.summary}</div></div>',
            unsafe_allow_html=True,
        )
        for key, label in SECTIONS:
            val = t.data.get(key)
            if not val:
                continue
            st.markdown(f'<div class="ps-kv" style="margin-top:.6rem;">{label}</div>',
                        unsafe_allow_html=True)
            if key == "sigma":
                st.code(val, language="yaml")
            elif key == "yara":
                st.code(val, language="c")
            elif isinstance(val, list):
                for item in val:
                    st.markdown(f"- {item}")
            else:
                st.markdown(val)
