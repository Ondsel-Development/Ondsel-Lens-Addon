from dataclasses import dataclass
from typing import Optional

# target is one of:
#  'users'
#  'organizations'
#  'workspaces'
#  'shared-models'
#  'models'
#  'ondsel'

@dataclass(order=True)
class NavRef:
    target: str
    username: Optional[str] = None
    orgname: Optional[str] = None
    wsname: Optional[str] = None
    sharelinkid: Optional[str] = None
    modelId: Optional[str] = None

    def user_friendly_target_name(self):
        # visit https://github.com/Ondsel-Development/Ondsel-Server/blob/main/frontend/src/curationHelpers.js
        # for source of this
        match self.target:
            case "workspaces":
                return "workspace"
            case "organizations":
                return "organization"
            case "users":
                return "user"
            case "shared-models":
                return "share-link"
            case _:
                return "unknown"
