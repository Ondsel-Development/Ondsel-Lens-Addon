# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass
from typing import Optional, Union

from models.group_summary import GroupSummary
from models.user_summary import UserSummary


@dataclass(order=True)
class GroupsOrUsers:
    type: str
    permission: str
    groupOrUser: Union[UserSummary, GroupSummary]

    def __post_init__(self):
        if self.groupOrUser:
            if "username" in self.groupOrUser:
                self.groupOrUser = UserSummary(**self.groupOrUser)
            else:
                self.groupOrUser = GroupSummary(**self.groupOrUser)
