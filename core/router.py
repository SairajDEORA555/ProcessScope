"""Maps module IDs to module instances and tracks which one is active.

The app calls router.render_active(); the sidebar calls router.navigate(id).
Neither knows anything about specific modules — they only speak this interface.
"""
from typing import List
from modules.base_module import BaseModule
from core.state import AppState


class Router:
    def __init__(self, modules: List[BaseModule]) -> None:
        self._modules = {m.id: m for m in modules}
        self._order = [m.id for m in modules]

    @property
    def modules(self) -> List[BaseModule]:
        return [self._modules[mid] for mid in self._order]

    @property
    def active_id(self) -> str:
        current = AppState.get("active_module")
        if current not in self._modules:
            current = self._order[0]
            AppState.set("active_module", current)
        return current

    def navigate(self, module_id: str) -> None:
        if module_id in self._modules:
            AppState.set("active_module", module_id)

    def render_active(self) -> None:
        self._modules[self.active_id].render()
