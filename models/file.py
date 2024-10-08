import inspect
from dataclasses import dataclass, field
from typing import Optional, Any

import Utils
from models.directory_summary import DirectorySummary
from models.file_version import FileVersion
from models.model_summary import ModelSummary
from models.share_link_summary import ShareLinkSummary
from models.user_summary import UserSummary
from models.workspace_summary import WorkspaceSummary


@dataclass(order=True)
class File:
    """
    A File is ... a file. It is not necessarily a CAD model. It has versions forming a commit history.
    Files only exist within a single workspace.
    A file may have zero or more ShareLinks and Models associated with it.
    """

    _id: str
    custFileName: str
    currentVersionId: str
    userId: str
    modelId: Optional[str]
    model: ModelSummary
    isSystemGenerated: Optional[bool]
    createdAt: int
    updatedAt: int
    directory: Optional[DirectorySummary]
    workspace: Optional[WorkspaceSummary]
    versions: list[FileVersion] = field(default_factory=list, repr=False)
    relatedUserDetails: list[UserSummary] = field(default_factory=list, repr=False)
    followingActiveSharedModels: list[ShareLinkSummary] = field(
        default_factory=list, repr=False
    )

    def __post_init__(self):
        self.model = ModelSummary(**self.model)
        if self.directory is not None:
            self.directory = DirectorySummary(**self.directory)
        if self.workspace is not None:
            self.workspace = WorkspaceSummary(**self.workspace)
        self.versions = Utils.convert_to_class_list(self.versions, FileVersion)
        self.relatedUserDetails = Utils.convert_to_class_list(
            self.relatedUserDetails, UserSummary
        )
        self.followingActiveSharedModels = Utils.convert_to_class_list(
            self.followingActiveSharedModels, ShareLinkSummary
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
