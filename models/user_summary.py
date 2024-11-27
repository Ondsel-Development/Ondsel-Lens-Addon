# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass


@dataclass(order=True)
class UserSummary:
    _id: str
    username: str
    name: str
    tier: str
