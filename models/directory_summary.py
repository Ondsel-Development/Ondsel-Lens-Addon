from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class DirectorySummary:
    _id: str
    name: str
