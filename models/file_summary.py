from dataclasses import dataclass
from models.file_version import FileVersion
from typing import Optional


@dataclass(order=True)
class FileSummary:
    _id: str
    custFileName: str
    modelId: str
    currentVersion: FileVersion
    thumbnailUrlCache: Optional[str] = None

    def __post_init__(self):
        self.currentVersion = FileVersion(**self.currentVersion)


# the "Limited" variant is to prevent recursive references and simplify data structures
@dataclass(frozen=True, order=True)
class FileSummary_CurationLimited:
    _id: str
    custFileName: str
    modelId: str
    currentVersion: ...
    thumbnailUrlCache: Optional[str] = None
