"""Loads JSON datasets from the project's data/ directory.

Centralising file access here means modules never hardcode paths, and we can
later swap JSON for SQLite behind the same interface (Dependency Inversion).
"""
import json
from pathlib import Path
from typing import Any, Optional


class JsonDataLoader:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is not None:
            self._base = Path(base_dir)
        else:
            # core/data_loader.py -> core -> project root -> data/
            self._base = Path(__file__).resolve().parent.parent / "data"

    def load(self, filename: str) -> Any:
        path = self._base / filename
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
