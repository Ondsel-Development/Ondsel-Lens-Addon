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
            case "models":
                return "CAD viewing"
            case _:
                return "unknown"

    def build_url_suffix(self):
        # visit https://github.com/Ondsel-Development/Ondsel-Server/blob/main/frontend/src/curationHelpers.js
        # for source of this
        url = "404"
        match self.target:
            case "workspaces":
                if self.orgname != None:
                    url = f"org/{self.orgname}/workspace/{self.wsname}"
                else:
                    url = f"user/{self.username}/workspace/{self.wsname}"
            case "organizations":
                url = f"org/{self.orgname}"
            case "users":
                url = f"user/{self.username}"
            case "shared-models":
                url = f"share/{self.sharelinkid}"
            case "models":
                url = f"model/{self.modelid}"
            case "ondsel":
                url = ""
        return url

    def generate_url(self, base):
        suffix = self.build_url_suffix()
        url = f"{base}{suffix}"
        return url
