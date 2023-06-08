from PySide.QtCore import Qt, QAbstractTableModel, QAbstractListModel, QModelIndex
from PySide import QtCore
import os
import json
import shutil

modPath = os.path.dirname(__file__).replace("\\", "/")

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

    def __init__(self, parent=None, filename=None):
        super(WorkspaceListModel, self).__init__(parent)
        self.workspaceListFile = (
            f"{modPath}/workspaceList.json" if filename is None else filename
        )

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

    def addWorkspace(self, workspaceName, workspaceDesc, workspaceType, workspaceUrl):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.workspaces.append(
            {
                "name": workspaceName,
                "description": workspaceDesc,
                "type": workspaceType,
                "url": workspaceUrl,
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

        for i in range(len(self.workspaces) - 1, -1, -1):
            if self.workspaces[i]["type"] == "Ondsel":
                # Delete the Ondsel local Folder
                try:
                    shutil.rmtree(self.workspaces[i]["url"])
                except FileNotFoundError:
                    print("Directory does not exist")

                self.workspaces.remove(self.workspaces[i])

        self.endResetModel()
        self.save()

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
