from dataclasses import dataclass
from file_version import FileVersion


@dataclass(frozen=True, order=True)
class FileSummary:
    _id: str
    custFileName: str
    modelId: str
    currentVersion: FileVersion
    thumbnailUrlCache: str = None


# the "Limited" variant is to prevent recursive references and simplify data structures
@dataclass(frozen=True, order=True)
class FileSummary_CurationLimited:
    _id: str
    custFileName: str
    modelId: str
    # currentVersion: FileVersion   # <-- we avoid deserializing all of this
    thumbnailUrlCache: str = None
