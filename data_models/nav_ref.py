from dataclasses import dataclass

# target is one of:
#  'users'
#  'organizations'
#  'workspaces'
#  'shared-models'
#  'models'
#  'ondsel'


@dataclass(frozen=True, order=True)
class NavRef:
    target: str
    username: str = None
    orgname: str = None
    wsname: str = None
    sharelinkid: str = None
    modelId: str = None
