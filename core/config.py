"""Application-wide configuration and design tokens.

Centralising colours here means the entire look of ProcessScope can be retuned
from one file. Switching from light to the Enterprise Dark theme is done purely
by changing the values below - no module code changes.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Design tokens for the Enterprise Dark theme."""
    bg: str = "#0F1117"
    surface: str = "#161B22"
    surface_alt: str = "#202938"
    border: str = "#2F3B52"
    text: str = "#F8FAFC"
    text_muted: str = "#94A3B8"
    accent: str = "#3B82F6"
    accent_hover: str = "#2F6FD6"
    accent_soft: str = "rgba(59,130,246,0.14)"
    success: str = "#22C55E"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    info: str = "#38BDF8"
    radius: str = "12px"
    shadow: str = "0 1px 2px rgba(0,0,0,.45), 0 12px 32px rgba(0,0,0,.30)"


class AppConfig:
    """Immutable, project-wide constants."""
    APP_NAME: str = "ProcessScope"
    TAGLINE: str = "Interactive Operating System Internals, Attack & Defense Simulator"
    VERSION: str = "0.1.0"
    PALETTE: Palette = Palette()
