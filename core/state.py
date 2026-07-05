"""A thin wrapper around Streamlit's session_state."""
import streamlit as st


class AppState:
    DEFAULTS = {
        "system_booted": False,
        "active_module": "home_dashboard",
    }

    @classmethod
    def init(cls) -> None:
        for key, value in cls.DEFAULTS.items():
            st.session_state.setdefault(key, value)

    @staticmethod
    def get(key: str, default=None):
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value) -> None:
        st.session_state[key] = value
