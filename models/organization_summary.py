# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass
from enum import StrEnum

from models.directory_summary import DirectorySummary


class OrganizationType(StrEnum):
    PERSONAL = "Personal"
    OPEN = "Open"
    PRIVATE = "Private"
    ONDSEL = "Ondsel"


@dataclass(frozen=True, order=True)
class OrganizationSummary:
    _id: str
    name: str
    refName: str
    type: OrganizationType
