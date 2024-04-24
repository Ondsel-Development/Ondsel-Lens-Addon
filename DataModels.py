# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************


import os
import json
from pathlib import Path

from PySide.QtCore import Qt, QAbstractListModel, QModelIndex
from PySide.QtGui import QStandardItemModel, QStandardItem

import FreeCAD


CACHE_PATH = FreeCAD.getUserCachePath() + "Ondsel-Lens/"
p = FreeCAD.ParamGet("User parameter:BaseApp/Ondsel")


class WorkspaceListModel(QAbstractListModel):
    """Workspaces is a list of dicts

        workspaces =
    [   {
            "name" : "myWorkspace",
            "description" : "This is my workspace description",
            "url" : "url",
            "type" : "local",
        },
    ]
    """

    def __init__(self, **kwargs):
        parent = kwargs.get("parent", None)
        super(WorkspaceListModel, self).__init__(parent)

        self.workspaceView = kwargs["WorkspaceView"]

        self.workspaceListFile = f"{CACHE_PATH}/workspaceList.json"

        self.refreshModel()

    def refreshModel(self):
        # raises an APIClientException
        self.beginResetModel()
        if self.workspaceView.isLoggedIn():
            self.workspaces = self.workspaceView.apiClient.getWorkspaces()

            self.save()
        else:
            self.load()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.workspaces)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.workspaces[index.row()]

        return None

    def updateData(self, workspaces):
        self.beginResetModel()
        self.workspaces = workspaces
        self.endResetModel()
        self.save()

    # def addWorkspace(self, workspaceName, workspaceDesc, workspaceType, workspaceUrl,
    #                  _id, organisation, rootDirectory):
    #     for workspace in reversed(self.workspaces):
    #         if workspace["name"] == workspaceName:
    #             if workspaceType == "Ondsel" and workspace["type"] == "Local":
    #                 workspace["type"] = "Ondsel"
    #                 self.save()
    #             return

    #     self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
    #     self.workspaces.append(
    #         {
    #             "name": workspaceName,
    #             "description": workspaceDesc,
    #             "type": workspaceType,
    #             "url": workspaceUrl,
    #             "_id": _id,
    #             "organizationId": organisation,
    #             "rootDirectory" : rootDirectory,
    #             "currentDirectory" : rootDirectory
    #         }
    #     )
    #     self.endInsertRows()
    #     self.save()

    # def removeWorkspace(self, index):
    #     if index.isValid() and 0 <= index.row() < len(self.workspaces):
    #         self.beginRemoveRows(QtCore.QModelIndex(), index.row(), index.row())
    #         del self.workspaces[index.row()]
    #         self.endRemoveRows()
    #         self.save()

    def removeWorkspaces(self):
        self.beginResetModel()
        self.workspaces = []
        self.endResetModel()

    def load(self):
        self.workspaces = []
        if os.path.exists(self.workspaceListFile):
            with open(self.workspaceListFile, "r") as file:
                dataStr = file.read()

            if dataStr:
                self.workspaces = json.loads(dataStr)

    def save(self):
        dirname = os.path.dirname(self.workspaceListFile)
        Path(dirname).mkdir(parents=True, exist_ok=True)
        with open(self.workspaceListFile, "w") as file:
            file.write(json.dumps(self.workspaces))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def dump(self):
        """
        useful for debugging.  This will return the contents in a printable form
        """
        for row in range(self.rowCount()):
            item_index = self.index(row)
            item_data = self.data(item_index, Qt.DisplayRole)
            print(item_data)


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


# Unused
class FilesData:
    """This class contains all the data of the workspaces and their files under the
    structure of a dictionary :
    [
        {
            "Name" : "myWorkspace",
            "Description" : "This is my workspace description",
            "Url" : "url",
            "Type" : "local",
            "Files" :
                [
                    {
                        "custFileName" : basename,
                        "localUrl" : url,
                        "isFolder" : False,
                        "versions" :
                            [
                                basename,
                                basename.fcbak,
                                ...
                            ],
                        "currentVersion" : basename
                        "sharingLinks" :
                            [

                            ]
                    }
                ]

            }
        {
            ...
        }
    ]
    """

    def __init__(self):
        self.loadData()

    def loadData(self):
        with open("filesData.txt", "r") as file:
            dataStr = file.read()

        if dataStr:
            self.data = json.loads(dataStr)
        else:
            self.data = []

    def saveData(self):
        with open("filesData.txt", "w") as file:
            file.write(json.dumps(self.data))
