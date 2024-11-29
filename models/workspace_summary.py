# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class WorkspaceSummary:
    _id: str
    name: str
    refName: str
    open: bool

    # this just keeps my IDE from throwing warnings about accessing a private (underscored) field. You can totally
    # access _id directly without problem
    @property
    def id(self):
        return self._id
