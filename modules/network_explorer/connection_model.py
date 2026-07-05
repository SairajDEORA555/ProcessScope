"""Domain layer for the Network Explorer.

ConnectionModel is one socket/connection; ConnectionRepository is the query
interface the UI uses (all connections, or all connections for one process).
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ConnectionModel:
    protocol: str
    local_addr: str
    local_port: str
    remote_addr: str
    remote_port: str
    state: str
    pid: int
    process: str
    service: str
    direction: str
    suspicious: bool
    note: str

    @classmethod
    def from_dict(cls, d: dict) -> "ConnectionModel":
        return cls(
            protocol=d["protocol"], local_addr=d["local_addr"], local_port=d["local_port"],
            remote_addr=d["remote_addr"], remote_port=d["remote_port"], state=d.get("state", ""),
            pid=d["pid"], process=d["process"], service=d.get("service", ""),
            direction=d.get("direction", ""), suspicious=d.get("suspicious", False),
            note=d.get("note", ""),
        )

    def endpoint(self) -> str:
        if self.state == "LISTENING":
            return f":{self.local_port} (LISTEN)"
        return f"{self.remote_addr}:{self.remote_port}"


class ConnectionRepository:
    def __init__(self, connections: List[ConnectionModel]) -> None:
        self._conns = list(connections)

    @classmethod
    def from_json(cls, loader, filename: str) -> "ConnectionRepository":
        raw = loader.load(filename)
        return cls([ConnectionModel.from_dict(item) for item in raw])

    def all(self) -> List[ConnectionModel]:
        return list(self._conns)

    def get(self, index: int) -> Optional[ConnectionModel]:
        if 0 <= index < len(self._conns):
            return self._conns[index]
        return None

    def by_pid(self, pid: int) -> List[ConnectionModel]:
        return [c for c in self._conns if c.pid == pid]
