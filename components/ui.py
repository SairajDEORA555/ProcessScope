"""Reusable UI helpers - the shared design system.

Every module composes these so the app keeps one consistent look. New component
helpers (drawers, timeline/alert cards) will be added alongside the modules that
use them (EDR, Investigation) to avoid unused code.
"""
import streamlit as st
from core.config import AppConfig

_P = AppConfig.PALETTE


def page_header(title: str, subtitle: str = "", pill: str = "") -> None:
    pill_html = f'<span class="ps-pill">{pill}</span>' if pill else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.6rem;">'
        f'<h1 class="ps-h1">{title}</h1>{pill_html}</div>'
        f'<p class="ps-sub">{subtitle}</p><hr style="margin:.6rem 0 1.1rem;'
        f'border:none;border-top:1px solid {_P.border};">',
        unsafe_allow_html=True,
    )


# Alias kept for the requested "SectionHeader" naming in the design system.
def section_header(title: str, subtitle: str = "", pill: str = "") -> None:
    page_header(title, subtitle, pill)


def status_badge(text: str, kind: str = "neutral") -> str:
    """Return badge HTML. kind: success | warning | critical | info | neutral."""
    kind = kind if kind in ("success", "warning", "critical", "info", "neutral") else "neutral"
    return f'<span class="ps-badge {kind}">{text}</span>'


def card(body_html: str) -> None:
    st.markdown(f'<div class="ps-card">{body_html}</div>', unsafe_allow_html=True)


def metric_cards(items) -> None:
    """Render a row of stat cards. items: list of (label, value, color_hex)."""
    for col, (label, value, color) in zip(st.columns(len(items)), items):
        col.markdown(
            f'<div class="ps-card" style="text-align:center;padding:.8rem;">'
            f'<div style="font-size:1.5rem;font-weight:700;color:{color};">{value}</div>'
            f'<div class="ps-kv">{label}</div></div>',
            unsafe_allow_html=True,
        )
