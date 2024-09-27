import inspect
from dataclasses import dataclass
from typing import Optional, Any

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
    fileId: str
    file: dict  # addon is not expanding on this for now with a proper class model
    createdAt: int
    updatedAt: int
    isObjGenerationInProgress: Optional[bool]
    isObjGenerated: Optional[bool]
    shouldStartObjGeneration: Optional[bool]
    attributes: Optional[dict]
    objUrl: str
    isSharedModel: Optional[bool]
    isThumbnailGenerated: Optional[bool]
    thumbnailUrl: str
    sharedModelId: Optional[str]
    isSharedModelAnonymousType: Optional[bool]
    # deleted: Type.Optional(Type.Boolean()), # will never see this field via API
    # latestLogErrorIdForObjGenerationCommand: logErrorIdType,  # these fields are for docker use in the cloud; ignore
    # latestLogErrorIdForFcstdExportCommand: logErrorIdType,
    # latestLogErrorIdForStepExportCommand: logErrorIdType,
    # latestLogErrorIdForStlExportCommand: logErrorIdType,
    # latestLogErrorIdForObjExportCommand: logErrorIdType,
    haveWriteAccess: bool
    errorMsg: Optional[ErrorMsg] = None
    user: Optional[Any] = None  # Type.Ref(userSchema), # addon is not expanding on this for now with a proper class model
    thumbnailUrlUpdatedAt: Optional[int] = None
    isExportFCStdGenerated: Optional[bool] = False
    isExportSTEPGenerated: Optional[bool] = False
    isExportSTLGenerated: Optional[bool] = False
    isExportOBJGenerated: Optional[bool] = False
    generatedFileExtensionForViewer: Optional[str] = False
    fileUpdatedAt: Optional[int] = None
    custFileName: Optional[str] = None
    uniqueFileName: Optional[str] = None  # deprecated; use file field

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
