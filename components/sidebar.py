"""Left navigation rail. Lists every registered module as a nav button and
highlights the active one. Purely data-driven off the router."""
import streamlit as st
from core.config import AppConfig
from core.router import Router


class Sidebar:
    def __init__(self, router: Router) -> None:
        self._router = router

    def render(self) -> None:
        with st.sidebar:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:.55rem;padding:.2rem 0 1rem;">'
                f'<div style="width:34px;height:34px;border-radius:9px;background:{AppConfig.PALETTE.accent};'
                f'color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;">&#9672;</div>'
                f'<div><div style="font-weight:700;font-size:1.05rem;">{AppConfig.APP_NAME}</div>'
                f'<div style="font-size:.7rem;color:#5b6470;">v{AppConfig.VERSION}</div></div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ps-kv" style="margin:.2rem 0 .4rem;">Modules</div>',
                        unsafe_allow_html=True)

            active = self._router.active_id
            for module in self._router.modules:
                is_active = module.id == active
                if st.button(
                    f"{module.icon}  {module.title}",
                    key=f"nav_{module.id}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    self._router.navigate(module.id)
                    st.rerun()
