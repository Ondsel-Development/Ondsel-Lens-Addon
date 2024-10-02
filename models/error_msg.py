from dataclasses import dataclass
from typing import Optional


@dataclass(order=True)
class ErrorMsg:
    code: int
    type: str
    detail: Optional[dict]
