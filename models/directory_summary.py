# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class DirectorySummary:
    _id: str
    name: str
