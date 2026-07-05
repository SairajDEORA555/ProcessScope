"""Domain layer for the Process Explorer.

ProcessModel is a typed, immutable representation of one process. ProcessRepository
is the query interface the UI talks to - it answers 'who are the roots?', 'who are
this PID's children?' without the UI ever touching raw JSON.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ProcessModel:
    pid: int
    ppid: int
    name: str
    user: str
    integrity: str
    path: str
    command_line: str
    signed: bool
    description: str
    typical_parent: str
    security_note: str

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessModel":
        return cls(**data)


class ProcessRepository:
    def __init__(self, processes: List[ProcessModel]) -> None:
        self._by_pid = {p.pid: p for p in processes}

    @classmethod
    def from_json(cls, loader, filename: str) -> "ProcessRepository":
        raw = loader.load(filename)
        return cls([ProcessModel.from_dict(item) for item in raw])

    def all(self) -> List[ProcessModel]:
        return list(self._by_pid.values())

    def get(self, pid) -> Optional[ProcessModel]:
        return self._by_pid.get(pid)

    def children(self, pid: int) -> List[ProcessModel]:
        return sorted(
            [p for p in self._by_pid.values() if p.ppid == pid and p.pid != pid],
            key=lambda p: p.pid,
        )

    def roots(self) -> List[ProcessModel]:
        pids = set(self._by_pid)
        return sorted(
            [p for p in self._by_pid.values() if p.ppid not in pids or p.ppid == p.pid],
            key=lambda p: p.pid,
        )
