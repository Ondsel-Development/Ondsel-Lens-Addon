# from APIClient import APIClient
from PySide.QtCore import (
    QAbstractListModel,
    Qt,
    QModelIndex,
    Signal,
    QFileSystemWatcher,
)
from PySide.QtGui import (
    QFileDialog,
)
import Utils
import os
import FreeCAD
import shutil


class WorkSpaceModelFactory:
    @staticmethod
    def createWorkspace(workspaceDict, **kwargs):
        print(workspaceDict)
        if workspaceDict["type"] == "Ondsel":
            return ServerWorkspaceModel(workspaceDict, **kwargs)
        elif workspaceDict["type"] == "Local":
            return LocalWorkspaceModel(workspaceDict, **kwargs)
        elif workspaceDict["type"] == "External":
            return None


class WorkSpaceModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    NameAndIsFolderRole = Qt.UserRole + 2
    IdRole = Qt.UserRole + 3
    NameStatusAndIsFolderRole = Qt.UserRole + 4
    subPath = ""

    def __init__(self, workspaceDict, **kwargs):
        parent = kwargs.get("parent", None)
        super().__init__(parent)

        self.name = workspaceDict["name"]
        self.path = workspaceDict["url"]
        self.subPath = ""
        self.workspacetype = workspaceDict["type"]
        self.files = []

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.refreshModel)
        self.watcher.directoryChanged.connect(self.refreshModel)
        self.watcher.addPath(self.path)

    def clearModel(self):
        self.beginResetModel()
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        self.endResetModel()

    def refreshModel(self):
        pass  # Implemented in subclasses

    def getLocalFiles(self):
        if not os.path.exists(self.getFullPath()):
            os.makedirs(self.getFullPath())
        files = os.listdir(self.getFullPath())
        local_files = []

        for basename in files:
            # First we add the folders, such that they appear first in the list.
            if os.path.isdir(Utils.joinPath(self.getFullPath(), basename)):
                file_item = FileItem(
                    basename,
                    self.getFullPath(),
                    True,
                    [],
                    "",
                    "",
                    "",
                    "",
                )
                local_files.append(file_item)

        for basename in files:
            # Then we add the files that are supported
            if Utils.isOpenableByFreeCAD(basename):
                # Retrieve file creation and modification dates
                file_path = Utils.joinPath(self.getFullPath(), basename)
                created_time = os.path.getctime(file_path)
                modified_time = os.path.getmtime(file_path)
                file_item = FileItem(
                    basename,
                    file_path,
                    False,
                    [basename],
                    basename,
                    created_time,
                    modified_time,
                    "Untracked",
                )
                local_files.append(file_item)

        return local_files

    def rowCount(self, parent=None):
        return len(self.files)

    def data(self, index, role=Qt.DisplayRole):
        pass  # Implemented in subclasses

    def getWorkspacePath(self):
        """Returns the path of the workspace including subpath"""
        if self.subPath == "":
            return self.name
        else:
            print(self.name)
            return Utils.joinPath(self.name, self.subPath)

    def getFullPath(self):
        if self.subPath == "":
            return self.path
        else:
            return Utils.joinPath(self.path, self.subPath)

    def openFile(self, index):
        pass  # Implemented in subclasses

    def roleNames(self):
        return {
            Qt.DisplayRole: b"display",
            self.NameRole: b"name",
            self.NameAndIsFolderRole: b"nameAndIsFolder",
            self.IdRole: b"id",
            self.NameStatusAndIsFolderRole: b"nameStatusAndIsFolderRole",
        }

    def deleteFile(self, index):

        fileName = self.data(index, WorkSpaceModel.NameRole)

        fileName = Utils.joinPath(self.getFullPath(), fileName)
        if os.path.isfile(fileName):
            os.remove(fileName)
        elif os.path.isdir(fileName):
            shutil.rmtree(fileName)

        self.refreshModel()

    def dump(self):
        """
        useful for debugging.  This will return the contents in a printable form
        """

        for file in self.files:
            print(file)


    # def dump(self):
    #     for row in range(self.rowCount()):
    #         # index = self.index(row, 0)
    #         file_item = self.files[row]
    #         print(f"File {row + 1}:")
    #         print(f"Basename: {file_item.basename}")
    #         print(f"Path: {file_item.path}")
    #         print(f"Is Folder: {file_item.is_folder}")
    #         print(f"Versions: {file_item.versions}")
    #         print(f"Current Version: {file_item.current_version}")
    #         print(f"Created At: {file_item.created_at}")
    #         print(f"Updated At: {file_item.updated_at}")
    #         print(f"Status: {file_item.status}")
    #         if file_item.model is not None:
    #             model = file_item.model
    #             print(f"ID: {model['_id']}")
    #             print(f"Customer File Name: {model['custFileName']}")
    #             print(f"Unique File Name: {model['uniqueFileName']}")
    #             print(f"Created At: {model['createdAt']}")
    #             print(f"Updated At: {model['updatedAt']}")
    #             print(f"Is Shared Model: {model['isSharedModel']}")
    #             print(f"Attributes: {model['attributes']}")
    #             print(f"Object URL: {model['objUrl']}")
    #             print(f"Thumbnail URL: {model['thumbnailUrl']}")
    #         print()


class LocalWorkspaceModel(WorkSpaceModel):
    def __init__(self, workspaceDict, **kwargs):
        super().__init__(workspaceDict, **kwargs)

        self.refreshModel()
        self.refreshModel()

    def refreshModel(self):
        self.clearModel()
        if not os.path.isdir(self.path):
            self.files = []
            return

        self.beginResetModel()
        self.files = self.getLocalFiles()
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        file_item = self.files[index.row()]

        if role == Qt.DisplayRole:
            return file_item
        elif role == self.NameRole:
            return file_item.name
        elif role == self.NameAndIsFolderRole:
            return file_item.name, file_item.is_folder
        elif role == self.IdRole:
            return 0
        elif role == self.NameStatusAndIsFolderRole:
            return file_item.name, "", file_item.is_folder

        return None

    def openParentFolder(self):
        self.subPath = os.path.dirname(self.subPath)
        self.refreshModel()

    def openFile(self, index):
        file_item = self.files[index.row()]
        if file_item.is_folder:
            self.subPath = Utils.joinPath(self.subPath, file_item.name)
            print(self.subPath)
            self.refreshModel()
        else:
            file_path = Utils.joinPath(self.getFullPath(), file_item.name)
            FreeCAD.loadFile(file_path)


class ServerWorkspaceModel(WorkSpaceModel):

    def __init__(self, workspaceDict, **kwargs):
        super().__init__(workspaceDict, **kwargs)

        self.API_Client = kwargs["API_Client"]
        self.refreshModel()

        # if the folder doesnt exist, create it
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def refreshModel(self):
        self.clearModel()

        files = self.getLocalFiles()

        remoteFilesToAdd = []
        models = self.API_Client.getModels()
        for model in models:
            foundLocal = False
            for i, localFile in enumerate(files):
                if model["custFileName"] == localFile.name:
                    localFile.model = model

                    if model["updatedAt"] < localFile.updatedAt:
                        localFile.status = "ToUpload"

                    elif model["updatedAt"] > localFile.updatedAt:
                        localFile.status = "ToDownload"

                    else:
                        localFile.status = "Synced"
                    foundLocal = True
                    break
            if not foundLocal: # local doesnt have this file
                file_item = FileItem(
                    model["custFileName"],
                    self.getFullPath(),
                    False,
                    [model["custFileName"]],
                    model["custFileName"],
                    model["createdAt"],
                    model["updatedAt"],
                    "ToDownload",
                    model,
                )
                remoteFilesToAdd.append(file_item)
        files += remoteFilesToAdd

        self.beginResetModel()
        self.files = files
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        file_item = self.files[index.row()]

        if role == Qt.DisplayRole:
            return file_item
        elif role == self.NameRole:
            return file_item.name
        elif role == self.NameAndIsFolderRole:
            return file_item.name, False
        elif role == self.IdRole:
            if file_item.model is not None:
                return file_item.model["_id"]
        elif role == self.NameStatusAndIsFolderRole:
            return file_item.name, file_item.status, False

        return None

    def openFile(self, index):
        file_item = self.files[index.row()]
        if file_item.is_folder:
            self.subPath = Utils.joinPath(self.subPath, file_item.name)
            self.refreshModel()
        else:
            file_path = Utils.joinPath(self.getFullPath(), file_item.name)
            if not os.path.isfile(file_path):
                # download the file
                self.API_Client.downloadFileFromServer(
                    file_item.model["uniqueFileName"], file_path
                )

            FreeCAD.loadFile(file_path)

    def deleteFile(self, index):
        fileId = self.data(index, WorkSpaceModel.IdRole)
        if fileId is not None:
            self.API_Client.deleteModel(fileId)

        super.deleteFile(index)


class FileItem:
    def __init__(
        self,
        name,
        path,
        is_folder,
        versions,
        current_version,
        createdAt,
        updatedAt,
        status="Untracked",
        model=None,
    ):
        self.name = name
        self.path = path
        self.is_folder = is_folder
        self.versions = versions
        self.current_version = current_version
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.status = status
        self.model = model
