import json
import os
from pathlib import Path

from PySide.QtCore import QAbstractListModel, QModelIndex, Qt

from APIClient import fancy_handle, APICallResult
from Utils import CACHE_PATH


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

        self.api = kwargs["api"]

        self.workspaceListFile = f"{CACHE_PATH}/workspaceList.json"

        self.refreshModel()

    def set_api(self, api):
        self.api = api

    def refreshModel(self):
        def try_get_workspaces_connected():
            self.workspaces = self.api.getWorkspaces()

        self.beginResetModel()
        api_result = fancy_handle(try_get_workspaces_connected)
        if api_result == APICallResult.OK:
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
