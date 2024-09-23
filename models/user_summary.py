from dataclasses import dataclass


@dataclass(order=True)
class UserSummary:
    _id: str
    username: str
    name: str
    tier: str
