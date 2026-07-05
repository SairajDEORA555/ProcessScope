"""Domain layer for the Attack Simulator.

AttackStage is one kill-chain step; AttackModel bundles the stages with the
artifacts (processes, connections, registry, events, IOCs) the attack produces.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AttackStage:
    order: int
    name: str
    action: str
    detail: str

    @classmethod
    def from_dict(cls, d: dict) -> "AttackStage":
        return cls(order=d["order"], name=d["name"], action=d["action"], detail=d["detail"])


@dataclass(frozen=True)
class AttackModel:
    id: str
    name: str
    tactic: str
    technique: str
    severity: str
    description: str
    stages: List[AttackStage]
    processes: list
    connections: list
    registry: list
    events: list
    iocs: list

    @classmethod
    def from_dict(cls, d: dict) -> "AttackModel":
        return cls(
            id=d["id"], name=d["name"], tactic=d["tactic"], technique=d["technique"],
            severity=d["severity"], description=d["description"],
            stages=[AttackStage.from_dict(s) for s in d["stages"]],
            processes=d.get("processes", []), connections=d.get("connections", []),
            registry=d.get("registry", []), events=d.get("events", []), iocs=d.get("iocs", []),
        )


class AttackRepository:
    def __init__(self, attacks: List[AttackModel]) -> None:
        self._attacks = attacks
        self._by_id = {a.id: a for a in attacks}

    @classmethod
    def from_json(cls, loader, filename: str) -> "AttackRepository":
        raw = loader.load(filename)
        return cls([AttackModel.from_dict(item) for item in raw])

    def all(self) -> List[AttackModel]:
        return list(self._attacks)

    def get(self, attack_id) -> Optional[AttackModel]:
        return self._by_id.get(attack_id)

    def tactics(self) -> List[str]:
        return sorted({a.tactic for a in self._attacks})
