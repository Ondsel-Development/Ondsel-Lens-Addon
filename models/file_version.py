from dataclasses import dataclass


@dataclass(order=True)
class FileVersion:
    _id: str
    createdAt: int
    uniqueFileName: str = None
    userId: str = None
    message: str = None
    thumbnailUrlCache: str = None
    fileUpdatedAt: int = None
    lockedSharedModels: ... = None  # TODO: add this later


# TODO: add date text display for createdAt and fileUpdatedAt
