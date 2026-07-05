"""Domain layer for the Registry Explorer.

RegistryKeyModel is a typed key (with its values and metadata). RegistryNode is
a tree node; RegistryRepository assembles the flat key paths into a hive tree,
synthesising the intermediate container keys automatically.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RegistryKeyModel:
    path: str
    category: str
    persistence: bool
    mitre: str
    description: str
    security_note: str
    values: list

    @classmethod
    def from_dict(cls, d: dict) -> "RegistryKeyModel":
        return cls(
            path=d["path"],
            category=d.get("category", ""),
            persistence=d.get("persistence", False),
            mitre=d.get("mitre", ""),
            description=d.get("description", ""),
            security_note=d.get("security_note", ""),
            values=d.get("values", []),
        )


class RegistryNode:
    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path
        self.model: Optional[RegistryKeyModel] = None
        self.children: dict = {}


class RegistryRepository:
    def __init__(self, keys: List[RegistryKeyModel]) -> None:
        self._by_path = {k.path: k for k in keys}
        self._roots: dict = {}
        self._build_tree(keys)

    @classmethod
    def from_json(cls, loader, filename: str) -> "RegistryRepository":
        raw = loader.load(filename)
        return cls([RegistryKeyModel.from_dict(item) for item in raw])

    def _build_tree(self, keys: List[RegistryKeyModel]) -> None:
        for key in keys:
            segments = key.path.split("\\")
            parent = None
            accum = ""
            for i, seg in enumerate(segments):
                accum = seg if i == 0 else accum + "\\" + seg
                container = self._roots if parent is None else parent.children
                node = container.get(seg)
                if node is None:
                    node = RegistryNode(seg, accum)
                    container[seg] = node
                parent = node
            parent.model = key

    def all_keys(self) -> List[RegistryKeyModel]:
        return list(self._by_path.values())

    def categories(self) -> List[str]:
        return sorted({k.category for k in self._by_path.values() if k.category})

    def get(self, path) -> Optional[RegistryKeyModel]:
        return self._by_path.get(path)

    def roots(self) -> List[RegistryNode]:
        return sorted(self._roots.values(), key=lambda n: n.name)

    def get_node(self, path: str) -> Optional[RegistryNode]:
        if not path:
            return None
        segments = path.split("\\")
        node = self._roots.get(segments[0])
        for seg in segments[1:]:
            if node is None:
                return None
            node = node.children.get(seg)
        return node
