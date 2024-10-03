from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class WorkspaceSummary:
    _id: str
    name: str
    refName: str
    open: bool
