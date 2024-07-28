from dataclasses import dataclass


@dataclass(order=True)
class FileVersion:
    _id: str
    uniqueFileName: str = None
    userId: str = None
    message: str = None
    createdAt: int
    thumbnailUrlCache: str = None
    fileUpdatedAt: int = None
    # TODO:
    # lockedSharedModels: Type.Optional(Type.Array(sharedModelsSummarySchema)),


# TODO: add date text display for createdAt and fileUpdatedAt
