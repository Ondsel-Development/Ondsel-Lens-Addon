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
