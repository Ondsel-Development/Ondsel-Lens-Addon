# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

import inspect
from dataclasses import dataclass, field

import Utils
from models.nav_ref import NavRef
from models.file_summary import FileSummary_CurationLimited
from typing import Optional, Any
from PySide.QtCore import Qt, QAbstractListModel
from models.workspace_summary import WorkspaceSummary


@dataclass(order=True)
class Curation:
    _id: str
    collection: str
    nav: NavRef
    name: str = ""
    slug: str = ""
    description: str = ""
    longDescriptionMd: str = ""
    tags: list[str] = field(default_factory=list, repr=False)
    representativeFile: Optional[FileSummary_CurationLimited] = None
    promoted: Optional[Any] = field(
        default_factory=list, repr=False
    )  # This needs to be refactored later
    keywordRefs: Any = None  # ignore, not relevant to Add-On

    def __post_init__(self):
        self.nav = NavRef(**self.nav)
        if self.representativeFile:
            self.representativeFile = FileSummary_CurationLimited(
                **self.representativeFile
            )

    def is_downloadable(self):
        return (self.nav.target == "shared-models") or self.nav.target == "workspaces"

    def get_thumbnail_url(self):
        """either returns a full URL to a web thumbnail or a local svg filename. an URL will have a colon"""
        url = None
        if self.representativeFile:
            url = self.representativeFile.thumbnailUrlCache
        if url is None:
            url = self.get_just_icon_filename()
        return url

    def get_just_icon_filename(self):
        url = None
        if self.nav.target == "workspaces":
            url = "folder.svg"
        elif self.nav.target == "organizations":
            url = "group.svg"
        elif self.nav.target == "users":
            url = "person.svg"
        elif self.nav.target == "shared-models":
            url = "public.svg"
        elif self.nav.target == "models":
            url = None
        elif self.nav.target == "ondsel":
            url = None
        return url

    def generateWorkspaceSummary(self, open: bool):
        """create a WorkspaceSummary object for the current curation; as far as is practical"""
        ws = WorkspaceSummary(
            _id=self._id, name=self.name, refName=self.slug, open=open
        )
        return ws

    @classmethod
    def from_json(cls, json_data):
        return Utils.import_json_forgiving_of_extra_fields(cls, json_data)


class CurationListModel(QAbstractListModel):

    CurationRole = Qt.UserRole + 1

    def __init__(self, *args, curations=None, **kwargs):
        super(CurationListModel, self).__init__(*args, **kwargs)
        self.curation_list = curations or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.curation_list[index.row()].name
        elif role == self.CurationRole:
            return self.curation_list[index.row()]

    def rowCount(self, index):
        return len(self.curation_list)
