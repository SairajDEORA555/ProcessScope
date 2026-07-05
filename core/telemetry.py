"""TelemetryStore - the bridge between the Attack Simulator and the defensive
modules (EDR, SOC). Attacks WRITE artifacts here; EDR/SOC only READ them.

Backed by session state so it persists across page navigation within a session.
"""
import datetime
from core.state import AppState


class TelemetryStore:
    KEY = "telemetry"

    @staticmethod
    def _empty() -> dict:
        return {"attacks": [], "alerts": [], "events": [],
                "processes": [], "connections": [], "registry": []}

    @classmethod
    def _data(cls) -> dict:
        d = AppState.get(cls.KEY)
        if not d:
            d = cls._empty()
            AppState.set(cls.KEY, d)
        return d

    @classmethod
    def is_recorded(cls, attack_id: str) -> bool:
        return any(a["id"] == attack_id for a in cls._data()["attacks"])

    @classmethod
    def record(cls, attack) -> bool:
        d = cls._data()
        if cls.is_recorded(attack.id):
            return False
        base = datetime.datetime.now()
        start = len(d["events"])

        def stamp(i: int) -> str:
            return (base + datetime.timedelta(seconds=i * 2)).strftime("%H:%M:%S")

        d["attacks"].append({"id": attack.id, "name": attack.name})
        d["alerts"].append({
            "id": attack.id, "name": attack.name, "severity": attack.severity,
            "tactic": attack.tactic, "technique": attack.technique,
            "description": attack.description, "time": base.strftime("%H:%M:%S"),
            "iocs": attack.iocs,
        })
        for i, ev in enumerate(attack.events):
            d["events"].append({
                "time": stamp(start + i), "attack": attack.name, "severity": attack.severity,
                "event_id": ev["event_id"], "source": ev["source"], "message": ev["message"],
            })
        for p in attack.processes:
            d["processes"].append({**p, "attack": attack.name})
        for c in attack.connections:
            d["connections"].append({**c, "attack": attack.name})
        for r in attack.registry:
            d["registry"].append({**r, "attack": attack.name})
        AppState.set(cls.KEY, d)
        return True

    @classmethod
    def clear(cls) -> None:
        AppState.set(cls.KEY, cls._empty())

    @classmethod
    def alerts(cls):
        return cls._data()["alerts"]

    @classmethod
    def events(cls):
        return cls._data()["events"]

    @classmethod
    def processes(cls):
        return cls._data()["processes"]

    @classmethod
    def connections(cls):
        return cls._data()["connections"]

    @classmethod
    def registry(cls):
        return cls._data()["registry"]

    @classmethod
    def attacks(cls):
        return cls._data()["attacks"]
