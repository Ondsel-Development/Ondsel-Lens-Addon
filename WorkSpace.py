# from APIClient import APIClient
from PySide.QtCore import (
    QAbstractListModel,
    Qt,
    QModelIndex,
    Signal,
    QFileSystemWatcher,
    QThread,
)
from PySide.QtGui import (
    QPixmap,
)
import Utils
import os
import FreeCAD
import shutil
import uuid
import requests


class WorkSpaceModelFactory:
    @staticmethod
    def createWorkspace(workspaceDict, **kwargs):
        if workspaceDict["type"] == "Ondsel":
            return ServerWorkspaceModel(workspaceDict, **kwargs)
        elif workspaceDict["type"] == "Local":
            return LocalWorkspaceModel(workspaceDict, **kwargs)
        elif workspaceDict["type"] == "External":
            return None


class TokenRefreshThread(QThread):
    token_refreshed = Signal()

    def run(self):
        while True:
            self.token_refreshed.emit()
            self.sleep(600)


class WorkSpaceModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    NameAndIsFolderRole = Qt.UserRole + 2
    IdRole = Qt.UserRole + 3
    NameStatusAndIsFolderRole = Qt.UserRole + 4
    StatusRole = Qt.UserRole + 5
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
            if os.path.isdir(Utils.joinPath(self.getFullPath(), basename)) and not basename.startswith('.'):
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
                created_time = Utils.getFileCreateddAt(file_path)
                modified_time = Utils.getFileUpdatedAt(file_path)
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
            self.StatusRole: b"statusRole",
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


class LocalWorkspaceModel(WorkSpaceModel):
    def __init__(self, workspaceDict, **kwargs):
        super().__init__(workspaceDict, **kwargs)

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
        elif role == self.StatusRole:
            return ""
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

        # Create an instance of the token refresh thread
        self.refresh_thread = TokenRefreshThread()
        self.refresh_thread.token_refreshed.connect(self.refreshModel)
        self.refresh_thread.start()

    def refreshModel(self, firstCall=True):
        self.clearModel()

        files = self.getLocalFiles()

        remoteFilesToAdd = []
        models = self.API_Client.getModels()
        for model in models:
            foundLocal = False
            for i, localFile in enumerate(files):
                if model["custFileName"] == localFile.name:
                    localFile.model = model
                    serverDate = model["file"]["currentVersion"]["additionalData"]["fileUpdatedAt"]
                    localDate = localFile.updatedAt
                    # print(f"update date are : {serverDate} - {localDate}")
                    if serverDate < localDate:
                        localFile.status = "Server copy outdated"

                    elif serverDate > localDate:
                        localFile.status = "Local copy outdated"

                    else:
                        localFile.status = "Synced"
                    foundLocal = True
                    break
            if not foundLocal:  # local doesnt have this file
                file_item = FileItem(
                    model["custFileName"],
                    self.getFullPath(),
                    False,
                    [model["custFileName"]],
                    model["custFileName"],
                    model["createdAt"],
                    model["updatedAt"],
                    "Server only",
                    model,
                )
                remoteFilesToAdd.append(file_item)
        files += remoteFilesToAdd

        self.beginResetModel()
        self.files = files
        self.endResetModel()

        if firstCall:
            self.uploadUntrackedFiles()

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
        elif role == self.StatusRole:
            return file_item.status
        elif role == self.NameStatusAndIsFolderRole:
            return file_item.name, file_item.status, False

        return None

    def getServerThumbnail(self, fileId):
        for file_item in self.files:
            if file_item.model is not None and file_item.model["_id"] == fileId:
                thumbnailUrl = file_item.model["thumbnailUrl"]
                try:
                    response = requests.get(thumbnailUrl)
                    image_data = response.content
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)

                    # Crop the image to a square
                    width = pixmap.width()
                    height = pixmap.height()
                    size = min(width, height)
                    diff = abs(width - height)
                    left = diff // 2
                    pixmap = pixmap.copy(left, 0, size, size)

                    pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
                    return pixmap
                except requests.exceptions.RequestException as e:
                    pass # no thumbnail online.

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

        super().deleteFile(index)

    def downloadFile(self, index):
        # This will download the latest version.
        print("downloading file...")
        file_item = self.files[index.row()]
        if file_item.is_folder:
            print("Download of folders not supported yet.")
        else:
            file_path = Utils.joinPath(self.getFullPath(), file_item.name)
            self.API_Client.downloadFileFromServer(
                file_item.model["uniqueFileName"], file_path
            )
        self.refreshModel()

    def uploadFile(self, index):
        print("uploading file...")
        file_item = self.files[index.row()]
        if file_item.is_folder:
            print("Upload of folders not supported yet.")
        else:
            # unique file name is always generated even if file is already on the server under another uniqueFileName.
            uniqueName = f"{str(uuid.uuid4())}.fcstd"

            file_path = Utils.joinPath(self.getFullPath(), file_item.name)
            self.API_Client.uploadFileToServer(uniqueName, file_path)
            
            fileUpdateDate = Utils.getFileUpdatedAt(file_path)
            if file_item.model is None:
                # First time the file is uploaded.
                self.API_Client.createModel(file_item.name, fileUpdateDate, uniqueName)
            else:
                self.API_Client.regenerateModelObj(file_item.model["_id"], fileUpdateDate, uniqueName)

        self.refreshModel()

    def uploadUntrackedFiles(self):
        # This function upload untracked files automatically to Server.
        # It is called in refreshModel (and not only into addCurrentFile and addFiles)
        # in order to also catch when user add file manually to the folder.
        # A parameter to refreshModel is added to prevent infinite loops just in case.
        refreshRequired = False
        for file_item in self.files:
            if file_item.status == "Untracked":
                uniqueName = f"{str(uuid.uuid4())}.fcstd"
                file_path = Utils.joinPath(self.getFullPath(), file_item.name)
                fileUpdateDate = Utils.getFileUpdatedAt(file_path)
                self.API_Client.uploadFileToServer(uniqueName, file_path)
                self.API_Client.createModel(file_item.name, fileUpdateDate, uniqueName)
                refreshRequired = True

        if refreshRequired:
            self.refreshModel(False)

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
