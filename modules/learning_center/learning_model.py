"""Domain layer for the Learning Center.

LearningTopic keeps the well-known fields plus a flexible `data` dict of the
remaining sections, so the UI can render them through a fixed template.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LearningTopic:
    id: str
    title: str
    category: str
    summary: str
    data: dict

    @classmethod
    def from_dict(cls, d: dict) -> "LearningTopic":
        base = {"id", "title", "category", "summary"}
        data = {k: v for k, v in d.items() if k not in base}
        return cls(id=d["id"], title=d["title"], category=d["category"],
                   summary=d["summary"], data=data)

    def haystack(self) -> str:
        parts = [self.title, self.category, self.summary]
        for v in self.data.values():
            parts.append(" ".join(v) if isinstance(v, list) else str(v))
        return " ".join(parts).lower()


class LearningRepository:
    def __init__(self, topics: List[LearningTopic]) -> None:
        self._topics = topics
        self._by_id = {t.id: t for t in topics}

    @classmethod
    def from_json(cls, loader, filename: str) -> "LearningRepository":
        raw = loader.load(filename)
        return cls([LearningTopic.from_dict(item) for item in raw])

    def all(self) -> List[LearningTopic]:
        return list(self._topics)

    def get(self, topic_id) -> Optional[LearningTopic]:
        return self._by_id.get(topic_id)

    def categories(self) -> List[str]:
        return sorted({t.category for t in self._topics})
