"""Domain layer for the Driver Explorer.

Same model/repository shape as the Process and Service explorers - a typed
DriverModel and a DriverRepository the UI queries.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class DriverModel:
    name: str
    display_name: str
    driver_type: str
    start_type: str
    status: str
    signed: bool
    signer: str
    path: str
    load_group: str
    hardware: str
    description: str
    security_note: str

    @classmethod
    def from_dict(cls, data: dict) -> "DriverModel":
        return cls(**data)


class DriverRepository:
    def __init__(self, drivers: List[DriverModel]) -> None:
        self._by_name = {d.name: d for d in drivers}

    @classmethod
    def from_json(cls, loader, filename: str) -> "DriverRepository":
        raw = loader.load(filename)
        return cls([DriverModel.from_dict(item) for item in raw])

    def all(self) -> List[DriverModel]:
        return list(self._by_name.values())

    def get(self, name) -> Optional[DriverModel]:
        return self._by_name.get(name)

    def types(self) -> List[str]:
        return sorted({d.driver_type for d in self._by_name.values()})
