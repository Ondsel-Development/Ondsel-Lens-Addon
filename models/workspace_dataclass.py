import inspect
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


from models.curation import Curation
from models.directory_summary import DirectorySummary
from models.groups_or_users import GroupsOrUsers
from models.organization_summary import OrganizationSummary, OrganizationType


class LicenseType(StrEnum):
    CC0 = "CC0 1.0"
    CC_BY = "CC BY 4.0"
    CC_BY_SA = "CC BY-SA 4.0"
    ARR = "All Rights Reserved"  # default license


@dataclass(order=True)
class WorkspaceDataClass:
    """ On the API and DB, this model is simply called `Workspace` or `workspaces`. But to prevent confusion in
    the add-on, it has been explicitly named `WorkspaceDataClass` here. """

    _id: str
    name: str
    refName: str
    open: bool
    description: str
    createdAt: int
    organizationId: str
    organization: OrganizationSummary
    rootDirectory: DirectorySummary
    curation: Optional[Curation]
    groupsOrUsers: list[GroupsOrUsers] = field(
        default_factory=list, repr=True
    )
    refNameHash: int = 0
    license: Optional[LicenseType] = LicenseType.ARR
    createdBy: str = None
    updatedAt: int = None
    # The "deleted*" fields will never appear on an API query
    # 'refNameHash', 'createdBy', and 'updatedAt' are given defaults because on "public" queries they
    # are omitted

    def __post_init__(self):
        self.organization = OrganizationSummary(**self.organization)
        self.rootDirectory = DirectorySummary(**self.rootDirectory)
        if self.curation:
            self.curation = Curation(**self.curation)
        new_gou_list = []
        for gou in self.groupsOrUsers:
            new_gou = GroupsOrUsers(**gou)
            new_gou_list.append(new_gou)
        self.groupsOrUsers = new_gou_list

    def describe_owner(self) -> str:
        name = "Unknown"
        print(self.organization)
        print(self.organization.type)
        orgType = self.organization.type
        if orgType == OrganizationType.OPEN:
            name = f"Org {self.organization.name}"
        elif orgType == OrganizationType.PRIVATE:
            name = f"Org {self.organization.name}"
        elif orgType == OrganizationType.PERSONAL:
            name = "User"
            if len(self.groupsOrUsers) > 0:
                name = f"User {self.groupsOrUsers[0].groupOrUser.name}"
        elif orgType == OrganizationType.ONDSEL:
            name = "Ondsel"
        return name

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

