"""Domain layer for Interactive Process Trees.

ProcTreeNode is a scored process; ProcTreeScenario is one tree (with roots/
children helpers); the repository loads the keyed scenarios.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ProcTreeNode:
    pid: int
    ppid: int
    name: str
    user: str
    cmdline: str
    verdict: str
    reason: str
    technique: str

    @classmethod
    def from_dict(cls, d: dict) -> "ProcTreeNode":
        return cls(
            pid=d["pid"], ppid=d["ppid"], name=d["name"], user=d.get("user", ""),
            cmdline=d.get("cmdline", ""), verdict=d.get("verdict", "benign"),
            reason=d.get("reason", ""), technique=d.get("technique", ""),
        )


class ProcTreeScenario:
    def __init__(self, key: str, label: str, description: str, nodes: List[ProcTreeNode]) -> None:
        self.key = key
        self.label = label
        self.description = description
        self.nodes = nodes
        self._by_pid = {n.pid: n for n in nodes}

    @classmethod
    def from_dict(cls, key: str, d: dict) -> "ProcTreeScenario":
        nodes = [ProcTreeNode.from_dict(n) for n in d["nodes"]]
        return cls(key, d["label"], d.get("description", ""), nodes)

    def get(self, pid) -> Optional[ProcTreeNode]:
        return self._by_pid.get(pid)

    def children(self, pid: int) -> List[ProcTreeNode]:
        return sorted([n for n in self.nodes if n.ppid == pid and n.pid != pid],
                      key=lambda n: n.pid)

    def roots(self) -> List[ProcTreeNode]:
        pids = set(self._by_pid)
        return sorted([n for n in self.nodes if n.ppid not in pids], key=lambda n: n.pid)


class ProcTreeRepository:
    def __init__(self, scenarios: dict) -> None:
        self._scenarios = scenarios

    @classmethod
    def from_json(cls, loader, filename: str) -> "ProcTreeRepository":
        raw = loader.load(filename)
        scenarios = {k: ProcTreeScenario.from_dict(k, v) for k, v in raw.items()}
        return cls(scenarios)

    def scenarios(self) -> List[ProcTreeScenario]:
        return list(self._scenarios.values())

    def get(self, key) -> Optional[ProcTreeScenario]:
        return self._scenarios.get(key)
