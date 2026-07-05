"""Domain layer for the Defense Simulator - Windows incident-response scenarios."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ScenarioModel:
    id: str
    name: str
    severity: str
    target: str
    summary: str
    detection: dict
    process: dict
    legit: str
    parent_note: str
    modules_note: str
    registry: list
    services: list
    event_logs: list
    artifacts: list
    commands: dict
    mitre: list
    containment: dict
    eradication: list
    recovery: list
    best_practices: list
    notes: list

    @classmethod
    def from_dict(cls, d: dict) -> "ScenarioModel":
        return cls(
            id=d["id"], name=d["name"], severity=d["severity"], target=d["target"],
            summary=d["summary"], detection=d["detection"], process=d["process"],
            legit=d.get("legit", ""), parent_note=d.get("parent_note", ""),
            modules_note=d.get("modules_note", ""), registry=d.get("registry", []),
            services=d.get("services", []), event_logs=d.get("event_logs", []),
            artifacts=d.get("artifacts", []), commands=d.get("commands", {}),
            mitre=d.get("mitre", []), containment=d.get("containment", {}),
            eradication=d.get("eradication", []), recovery=d.get("recovery", []),
            best_practices=d.get("best_practices", []), notes=d.get("notes", []),
        )


class DefenseRepository:
    def __init__(self, scenarios: List[ScenarioModel]) -> None:
        self._scenarios = scenarios
        self._by_id = {s.id: s for s in scenarios}

    @classmethod
    def from_json(cls, loader, filename: str) -> "DefenseRepository":
        raw = loader.load(filename)
        return cls([ScenarioModel.from_dict(item) for item in raw])

    def all(self) -> List[ScenarioModel]:
        return list(self._scenarios)

    def get(self, scenario_id) -> Optional[ScenarioModel]:
        return self._by_id.get(scenario_id)
