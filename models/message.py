# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from dataclasses import dataclass


@dataclass(order=True)
class Message:
    _id: str
    createdAt: int
    createdBy: str  # _id of user that created message
    text: str
