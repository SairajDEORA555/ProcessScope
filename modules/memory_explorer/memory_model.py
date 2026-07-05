"""Domain layer for the Memory Explorer.

MemoryRegion is one region of a process's virtual address space. MemoryMapModel
is a whole process map; MemoryRepository loads the keyed collection of maps.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MemoryRegion:
    base: int
    base_hex: str
    size: int
    region_type: str
    protection: str
    state: str
    detail: str
    suspicious: bool
    note: str

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryRegion":
        return cls(
            base=int(d["base"], 16),
            base_hex=d["base"],
            size=d["size"],
            region_type=d["region_type"],
            protection=d["protection"],
            state=d["state"],
            detail=d["detail"],
            suspicious=d.get("suspicious", False),
            note=d.get("note", ""),
        )


@dataclass(frozen=True)
class MemoryMapModel:
    key: str
    label: str
    pid: int
    regions: List[MemoryRegion]

    @classmethod
    def from_dict(cls, key: str, d: dict) -> "MemoryMapModel":
        regions = [MemoryRegion.from_dict(r) for r in d["regions"]]
        return cls(key=key, label=d["label"], pid=d["pid"], regions=regions)


class MemoryRepository:
    def __init__(self, maps: dict) -> None:
        self._maps = maps

    @classmethod
    def from_json(cls, loader, filename: str) -> "MemoryRepository":
        raw = loader.load(filename)
        maps = {k: MemoryMapModel.from_dict(k, v) for k, v in raw.items()}
        return cls(maps)

    def processes(self) -> List[MemoryMapModel]:
        return list(self._maps.values())

    def get(self, key) -> Optional[MemoryMapModel]:
        return self._maps.get(key)
