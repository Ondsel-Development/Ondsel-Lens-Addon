from dataclasses import dataclass


@dataclass(order=True)
class FileDetail:
    fileId: str
    versionId: str = None
