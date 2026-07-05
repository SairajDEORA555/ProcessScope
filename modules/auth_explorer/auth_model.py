"""Domain layer for the Authentication Explorer.

AuthStep is one message in a protocol exchange; AuthFlowModel is a whole
protocol (actors + steps + attacks); AuthRepository loads the keyed flows.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AuthStep:
    order: int
    name: str
    actor_from: str
    actor_to: str
    message: str
    description: str
    security_note: str
    attack: str

    @classmethod
    def from_dict(cls, d: dict) -> "AuthStep":
        return cls(
            order=d["order"], name=d["name"], actor_from=d["actor_from"],
            actor_to=d["actor_to"], message=d["message"], description=d["description"],
            security_note=d["security_note"], attack=d.get("attack", ""),
        )


@dataclass(frozen=True)
class AuthFlowModel:
    key: str
    label: str
    actors: list
    steps: List[AuthStep]
    attacks: list

    @classmethod
    def from_dict(cls, key: str, d: dict) -> "AuthFlowModel":
        steps = [AuthStep.from_dict(s) for s in d["steps"]]
        return cls(key=key, label=d["label"], actors=d["actors"], steps=steps,
                   attacks=d.get("attacks", []))

    def actor_label(self, actor_id: str) -> str:
        for a in self.actors:
            if a["id"] == actor_id:
                return a["label"]
        return actor_id


class AuthRepository:
    def __init__(self, flows: dict) -> None:
        self._flows = flows

    @classmethod
    def from_json(cls, loader, filename: str) -> "AuthRepository":
        raw = loader.load(filename)
        flows = {k: AuthFlowModel.from_dict(k, v) for k, v in raw.items()}
        return cls(flows)

    def protocols(self) -> List[AuthFlowModel]:
        return list(self._flows.values())

    def get(self, key) -> Optional[AuthFlowModel]:
        return self._flows.get(key)
