# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import json

from PySide.QtCore import Qt
from PySide.QtGui import QStandardItemModel, QStandardItem

ROLE_TYPE = Qt.UserRole
ROLE_SHARE_MODEL_ID = Qt.UserRole + 1
TYPE_ORG = 0
TYPE_BOOKMARK = 1


def getBookmarkModel(apiClient):
    model = QStandardItemModel()

    def addBookmarks(item, orgSecondaryReferencesId):
        secRefs = apiClient.getSecondaryRefs(orgSecondaryReferencesId)

        for bookmark in secRefs["bookmarks"]:
            if bookmark["collectionName"] == "shared-models":
                summary = bookmark["collectionSummary"]
                bookmarkItem = QStandardItem(summary["custFileName"])
                bookmarkItem.setData(TYPE_BOOKMARK, ROLE_TYPE)
                bookmarkItem.setData(summary["_id"], ROLE_SHARE_MODEL_ID)
                item.appendRow(bookmarkItem)

    root = model.invisibleRootItem()
    if apiClient:
        orgs = apiClient.getOrganizations()
        for org in orgs:
            orgItem = QStandardItem(org["name"])
            orgItem.setData(TYPE_ORG, ROLE_TYPE)
            root.appendRow(orgItem)
            addBookmarks(orgItem, org["orgSecondaryReferencesId"])

    return model
