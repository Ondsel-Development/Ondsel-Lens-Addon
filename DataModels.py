# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

from PySide.QtCore import Qt, QAbstractTableModel, QAbstractListModel, QModelIndex
from PySide import QtCore
import os
import json
import shutil
import FreeCAD

cachePath = FreeCAD.getUserCachePath()
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

        self.WorkspaceView = kwargs["WorkspaceView"]

        self.workspaceListFile = f"{cachePath}/workspaceList.json"

        self.refreshModel()

    def refreshModel(self):
        if self.WorkspaceView.apiClient is not None:
            self.workspaces = self.WorkspaceView.apiClient.getWorkspaces()
            
            # Add keys that we need locally
            for workspace in self.workspaces:
                workspace["url"] = cachePath + workspace["_id"]
                
                organizationName = next((org['name'] for org in self.WorkspaceView.user["organizations"] if org['_id'] == workspace["organizationId"]), "")
                workspace["organizationName"] = organizationName
            self.save()
        else:
            self.load()

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

    """def addWorkspace(self, workspaceName, workspaceDesc, workspaceType, workspaceUrl, _id, organisation, rootDirectory):
        for workspace in reversed(self.workspaces):
            if workspace["name"] == workspaceName:
                if workspaceType == "Ondsel" and workspace["type"] == "Local":
                    workspace["type"] = "Ondsel"
                    self.save()
                return

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.workspaces.append(
            {
                "name": workspaceName,
                "description": workspaceDesc,
                "type": workspaceType,
                "url": workspaceUrl,
                "_id": _id,
                "organizationId": organisation,
                "rootDirectory" : rootDirectory,
                "currentDirectory" : rootDirectory
            }
        )
        self.endInsertRows()
        self.save()

    def removeWorkspace(self, index):
        if index.isValid() and 0 <= index.row() < len(self.workspaces):
            self.beginRemoveRows(QtCore.QModelIndex(), index.row(), index.row())
            del self.workspaces[index.row()]
            self.endRemoveRows()
            self.save()

    def removeOndselWorkspaces(self):
        self.beginResetModel()

        for workspace in reversed(self.workspaces):
            if workspace["type"] == "Ondsel":
                if p.GetBool("clearCache", False):
                    # Delete the Ondsel local Folder
                    try:
                        shutil.rmtree(workspace["url"])
                    except FileNotFoundError:
                        print("Directory does not exist")

                    self.workspaces.remove(workspace)
                else:
                    workspace["type"] = "Local"

        self.endResetModel()
        self.save()"""

    def load(self):
        self.workspaces = []
        if os.path.exists(self.workspaceListFile):
            with open(self.workspaceListFile, "r") as file:
                dataStr = file.read()

            if dataStr:
                self.workspaces = json.loads(dataStr)

    def save(self):
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


# Unused
class FilesData:
    """This class contains all the data of the workspaces and their files under the structure of a dictionary :
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
