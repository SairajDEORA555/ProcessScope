"""Domain layer for the Service Explorer.

Mirrors the Process Explorer's model/repository pattern so the codebase stays
predictable: a typed ServiceModel and a ServiceRepository the UI queries.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ServiceModel:
    name: str
    display_name: str
    description: str
    start_type: str
    status: str
    account: str
    binary_path: str
    host_group: str
    dependencies: Tuple[str, ...]
    hosting_pid: int
    security_note: str

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceModel":
        data = dict(data)
        data["dependencies"] = tuple(data.get("dependencies", []))
        return cls(**data)


class ServiceRepository:
    def __init__(self, services: List[ServiceModel]) -> None:
        self._by_name = {s.name: s for s in services}

    @classmethod
    def from_json(cls, loader, filename: str) -> "ServiceRepository":
        raw = loader.load(filename)
        return cls([ServiceModel.from_dict(item) for item in raw])

    def all(self) -> List[ServiceModel]:
        return list(self._by_name.values())

    def get(self, name) -> Optional[ServiceModel]:
        return self._by_name.get(name)

    def dependents(self, name: str) -> List[ServiceModel]:
        return sorted(
            [s for s in self._by_name.values() if name in s.dependencies],
            key=lambda s: s.display_name,
        )
