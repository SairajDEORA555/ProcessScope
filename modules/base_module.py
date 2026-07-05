"""The contract every ProcessScope module must fulfil.

This abstract base class is the backbone of the whole architecture. Because the
router only depends on THIS interface, we can add 12 more modules without ever
modifying core code. Add a subclass, register it, done.
"""
from abc import ABC, abstractmethod


class BaseModule(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        """Stable, URL-safe identifier, e.g. 'boot_simulator'."""

    @property
    @abstractmethod
    def title(self) -> str:
        """Human-readable name shown in the sidebar."""

    @property
    @abstractmethod
    def icon(self) -> str:
        """A single emoji/glyph used as the nav icon."""

    @property
    def description(self) -> str:
        """Optional one-line summary for the page header."""
        return ""

    @abstractmethod
    def render(self) -> None:
        """Draw the module's UI into the current Streamlit page."""
