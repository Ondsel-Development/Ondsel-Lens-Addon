from dataclasses import dataclass


@dataclass(order=True)
class Message:
    _id: str
    createdAt: int
    createdBy: str  # _id of user that created message
    text: str
