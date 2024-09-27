import inspect
from dataclasses import dataclass
from typing import Optional

from models.error_msg import ErrorMsg


@dataclass(order=True)
class Model:
    """
    A "Model" is a snapshot in time for a specific combination of:
        1. File Version
        2. ShareLink aka "shared-model'
        3. User Parameters for the File Revision's attributes (if any)
    """

    _id: str
    userId: str
    user: dict  # Type.Ref(userSchema), # addon is not expanding on this for now with a proper class model
    # uniqueFileName: Optional[str]  # deprecated; use file field
    fileId: str
    file: dict  # addon is not expanding on this for now with a proper class model
    createdAt: int
    updatedAt: int
    fileUpdatedAt: Optional[int]
    isObjGenerationInProgress: Optional[bool]
    isObjGenerated: Optional[bool]
    shouldStartObjGeneration: Optional[bool]
    attributes: Optional[dict]
    errorMsg: Optional[ErrorMsg]
    objUrl: str
    isSharedModel: Optional[bool]
    isThumbnailGenerated: Optional[bool]
    thumbnailUrl: str
    thumbnailUrlUpdatedAt: int
    isExportFCStdGenerated: Optional[bool]
    isExportSTEPGenerated: Optional[bool]
    isExportSTLGenerated: Optional[bool]
    isExportOBJGenerated: Optional[bool]
    sharedModelId: Optional[str]
    isSharedModelAnonymousType: Optional[bool]
    # deleted: Type.Optional(Type.Boolean()), # will never see this field via API
    # latestLogErrorIdForObjGenerationCommand: logErrorIdType,  # these fields are for docker use in the cloud; ignore
    # latestLogErrorIdForFcstdExportCommand: logErrorIdType,
    # latestLogErrorIdForStepExportCommand: logErrorIdType,
    # latestLogErrorIdForStlExportCommand: logErrorIdType,
    # latestLogErrorIdForObjExportCommand: logErrorIdType,
    generatedFileExtensionForViewer: Optional[str]
    haveWriteAccess: bool

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
