# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

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
        if self.target == "workspaces":
            return "workspace"
        elif self.target == "organizations":
            return "organization"
        elif self.target == "users":
            return "user"
        elif self.target == "shared-models":
            return "share-link"
        elif self.target == "models":
            return "CAD viewing"
        else:
            return "unknown"

    def build_url_suffix(self):
        # visit https://github.com/Ondsel-Development/Ondsel-Server/blob/main/frontend/src/curationHelpers.js
        # for source of this
        url = "404"
        if self.target == "workspaces":
            if self.orgname is not None:
                url = f"org/{self.orgname}/workspace/{self.wsname}"
            else:
                url = f"user/{self.username}/workspace/{self.wsname}"
        elif self.target == "organizations":
            url = f"org/{self.orgname}"
        elif self.target == "users":
            url = f"user/{self.username}"
        elif self.target == "shared-models":
            url = f"share/{self.sharelinkid}"
        elif self.target == "models":
            url = f"model/{self.modelid}"
        elif self.target == "ondsel":
            url = ""
        return url

    def generate_url(self, base):
        suffix = self.build_url_suffix()
        url = f"{base}{suffix}"
        return url
