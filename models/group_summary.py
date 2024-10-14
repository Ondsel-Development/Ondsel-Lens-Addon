from dataclasses import dataclass


@dataclass(order=True)
class GroupSummary:
    _id: str
    name: str
