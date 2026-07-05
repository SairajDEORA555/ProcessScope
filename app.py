"""ProcessScope - application entry point.

Flow: configure page -> inject theme -> init state -> if not booted, play the
startup splash and stop; otherwise build the router and render the active module.
"""
import streamlit as st

from core.config import AppConfig
from core.theme import inject_theme
from core.state import AppState
from core.router import Router
from components.boot_screen import BootScreen
from components.sidebar import Sidebar
from modules import get_registered_modules


def main() -> None:
    st.set_page_config(
        page_title=AppConfig.APP_NAME,
        page_icon="\u25c8",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    AppState.init()

    # Gate the entire app behind the animated boot sequence (plays once/session).
    if not AppState.get("system_booted"):
        BootScreen().render()
        return

    router = Router(get_registered_modules())
    Sidebar(router).render()
    router.render_active()


if __name__ == "__main__":
    main()
