from dataclasses import dataclass, field

import Utils
from models.directory_summary import DirectorySummary
from models.file_summary import FileSummary
from typing import Optional
from models.workspace_summary import WorkspaceSummary


@dataclass(order=True)
class Directory:
    _id: str
    name: str
    workspace: WorkspaceSummary = None
    createdBy: str = None  # ObjectId of User
    createdAt: int = None
    updatedAt: int = None
    files: list[FileSummary] = field(
        default_factory=list, repr=True
    )
    directories: list[DirectorySummary] = field(
        default_factory=list, repr=True
    )
    parentDirectory: Optional[DirectorySummary] = None
    # 'workspace', 'createdBy', 'createdAt', and 'updatedAt' have defaults because omitted on "public" queries

    def __post_init__(self):
        if self.workspace:
            self.workspace = WorkspaceSummary(**self.workspace)
        if self.parentDirectory:
            self.parentDirectory = DirectorySummary(**self.parentDirectory)
        self.files = Utils.convert_to_class_list(self.files, FileSummary)
        self.directories = Utils.convert_to_class_list(self.directories, DirectorySummary)

    @classmethod
    def from_json(cls, json_data):
        return Utils.import_json_forgiving_of_extra_fields(cls, json_data)
