import inspect
from dataclasses import dataclass
from typing import Optional, Any


@dataclass(order=True)
class ModelSummary:
    """
    A summary of a Model
    """

    _id: str
    createdAt: int
    isObjGenerated: Optional[bool]
    isThumbnailGenerated: Optional[bool]
    thumbnailUrlCache: str

    @classmethod
    def from_json(cls, json_data):
        """makes forgiving of extra fields"""
        return cls(
            **{
                k: v
                for k, v in json_data.items()
                if k in inspect.signature(cls).parameters
            }
        )
