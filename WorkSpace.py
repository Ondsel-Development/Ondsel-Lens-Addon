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
    QMessageBox,
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
            if os.path.isdir(
                Utils.joinPath(self.getFullPath(), basename)
            ) and not basename.startswith("."):
                file_item = FileItem(
                    basename,
                    "",
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
            # Then we add the files
            file_path = Utils.joinPath(self.getFullPath(), basename)
            if not os.path.isdir(file_path):
                created_time = Utils.getFileCreateddAt(file_path)
                modified_time = Utils.getFileUpdatedAt(file_path)
                base, extension = os.path.splitext(basename)
                if extension.lower() != ".fcbak":
                    file_item = FileItem(
                        basename,
                        extension.lower(),
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
            if Utils.isOpenableByFreeCAD(file_path):
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

        serverFilesToAdd = []
        serverFiles = self.API_Client.getFiles()
        for serverFileDict in serverFiles:
            try:
                serverDate = serverFileDict["currentVersion"]["additionalData"]["fileUpdatedAt"]
            except KeyError:
                serverDate = serverFileDict["currentVersion"]["createdAt"]

            foundLocal = False
            for i, localFile in enumerate(files):
                if serverFileDict["custFileName"] == localFile.name:
                    localFile.serverFileDict = serverFileDict
                    localDate = localFile.updatedAt
                    # print(f"update date are : {serverDate} - {localDate}")
                    if serverDate < localDate:
                        localFile.status = "Server copy outdated"

                    elif serverDate > localDate:
                        localFile.status = "Local copy outdated"

                    else:
                        localFile.status = "Synced"

                    if "modelId" in serverFileDict:
                        localFile.serverModelDict = self.API_Client.getModel(
                            serverFileDict["modelId"]
                        )

                    foundLocal = True
                    break
            if not foundLocal:  # local doesnt have this file
                serverModelDict = None
                if "modelId" in serverFileDict:
                    serverModelDict = self.API_Client.getModel(
                        serverFileDict["modelId"]
                    )

                base, extension = os.path.splitext(serverFileDict["custFileName"])
                file_item = FileItem(
                    serverFileDict["custFileName"],
                    extension.lower(),
                    self.getFullPath(),
                    False,
                    [serverFileDict["custFileName"]],
                    serverFileDict["custFileName"],
                    serverFileDict["createdAt"],
                    serverDate,
                    "Server only",
                    serverFileDict,
                    serverModelDict,
                )
                serverFilesToAdd.append(file_item)
        files += serverFilesToAdd

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
            if file_item.serverModelDict is not None:
                return file_item.serverModelDict["_id"]
        elif role == self.StatusRole:
            return file_item.status
        elif role == self.NameStatusAndIsFolderRole:
            return file_item.name, file_item.status, False

        return None

    def getServerThumbnail(self, fileId):
        for file_item in self.files:
            if (
                file_item.serverModelDict is not None
                and file_item.serverModelDict["_id"] == fileId
            ):
                thumbnailUrl = file_item.serverModelDict["thumbnailUrl"]
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
                    pass  # no thumbnail online.

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
                # Note: serverModelDict["uniqueFileName"] = asserverFileDict["currentVersion"]["uniqueFileName"]
                self.API_Client.downloadFileFromServer(
                    file_item.serverModelDict["uniqueFileName"], file_path
                )

            if Utils.isOpenableByFreeCAD(file_path):
                FreeCAD.loadFile(file_path)

    def deleteFile(self, index):
        file_item = self.files[index.row()]

        if file_item.serverModelDict is not None:
            self.API_Client.deleteModel(file_item.serverModelDict["_id"])
        else:
            self.API_Client.deleteFile(file_item.serverFileDict["_id"])

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
                file_item.serverModelDict["uniqueFileName"], file_path
            )
        self.refreshModel()

    def uploadFile(self, index):
        print("uploading file...")

        file_item = self.files[index.row()]
        if file_item.is_folder:
            print("Upload of folders not supported yet.")
        else:
            # First we refresh to make sure the file status have not changed.
            self.refreshModel()

            # Check if the file is not newer on the server first.
            if file_item.status == "Local copy outdated":
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Confirmation")
                msg_box.setText(
                    "The server version is newer than your local copy. Uploading will override the server version.\nAre you sure you want to proceed?"
                )
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)

                if msg_box.exec_() == QMessageBox.No:
                    return

            if file_item.serverModelDict is None:
                self.upload(file_item.name, True)
            else:
                self.upload(file_item.name, False, file_item.serverModelDict["_id"])

        self.refreshModel()

    def uploadUntrackedFiles(self):
        # This function upload untracked files automatically to Server.
        # It is called in refreshModel (and not only into addCurrentFile and addFiles)
        # in order to also catch when user add file manually to the folder.
        # A parameter to refreshModel is added to prevent infinite loops just in case.
        refreshRequired = False
        for file_item in self.files:
            if file_item.status == "Untracked":
                self.upload(file_item.name, True)
                refreshRequired = True

        if refreshRequired:
            self.refreshModel(False)

    def upload(self, fileName, create, id_=0):
        # unique file name is always generated even if file is already on the server under another uniqueFileName.
        base, extension = os.path.splitext(fileName)
        uniqueName = f"{str(uuid.uuid4())}.fcstd"  # TODO replace .fcstd by {extension}

        file_path = Utils.joinPath(self.getFullPath(), fileName)
        fileUpdateDate = Utils.getFileUpdatedAt(file_path)

        self.API_Client.uploadFileToServer(uniqueName, file_path)

        if create:
            # First time the file is uploaded.
            if extension.lower() in [".fcstd", ".obj"]:
                self.API_Client.createModel(fileName, fileUpdateDate, uniqueName)
            else:
                self.API_Client.createFile(fileName, fileUpdateDate, uniqueName)
        else:
            if extension.lower() in [".fcstd", ".obj"]:
                self.API_Client.regenerateModelObj(id_, fileUpdateDate, uniqueName)
            else:
                self.API_Client.updateFileObj(id_, fileUpdateDate, uniqueName)


class FileItem:
    def __init__(
        self,
        name,
        ext,
        path,
        is_folder,
        versions,
        current_version,
        createdAt,
        updatedAt,
        status="Untracked",
        serverFileDict=None,
        serverModelDict=None,
    ):
        self.name = name
        self.ext = ext
        self.path = path
        self.is_folder = is_folder
        self.versions = versions
        self.current_version = current_version
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.status = status
        self.serverFileDict = serverFileDict
        self.serverModelDict = serverModelDict
