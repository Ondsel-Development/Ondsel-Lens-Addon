import inspect
from dataclasses import dataclass, field

import Utils
from models.share_link_summary import ShareLinkSummary


@dataclass(order=True)
class FileVersion:
    _id: str
    createdAt: int
    uniqueFileName: str = None
    userId: str = None
    message: str = None
    thumbnailUrlCache: str = None
    fileUpdatedAt: int = None
    lockedSharedModels: list[ShareLinkSummary] = field(default_factory=list, repr=False)
    additionalData: dict = None

    def __post_init__(self):
        self.lockedSharedModels = Utils.listy_class_replacement(
            self.lockedSharedModels, ShareLinkSummary
        )

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


# TODO: add date text display for createdAt and fileUpdatedAt
