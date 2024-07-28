from dataclasses import dataclass
from file_version import FileVersion


@dataclass(frozen=True, order=True)
class FileSummary:
    _id: str
    custFileName: str
    modelId: str
    currentVersion: FileVersion
    thumbnailUrlCache: str = None
