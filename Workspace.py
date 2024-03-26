from PySide.QtCore import (
    QAbstractListModel,
    Qt,
    QModelIndex,
    Signal,
    QFileSystemWatcher,
    QThread,
)
from PySide.QtGui import QPixmap
import Utils
import os
import shutil
import uuid
import requests

from enum import Enum, auto

from inspect import cleandoc

from DataModels import CACHE_PATH

from VersionModel import VersionModel

logger = Utils.getLogger(__name__)

# class WorkspaceModelFactory:
#    @staticmethod
#    def createWorkspace(workspaceDict, **kwargs):
#        if workspaceDict["type"] == "Ondsel":
#            return ServerWorkspaceModel(workspaceDict, **kwargs)
#        elif workspaceDict["type"] == "Local":
#            return LocalWorkspaceModel(workspaceDict, **kwargs)
#        elif workspaceDict["type"] == "External":
#            return None


NO_REFRESH = False


class FileStatus(Enum):
    SERVER_ONLY = auto()
    SERVER_COPY_OUTDATED = auto()
    LOCAL_COPY_OUTDATED = auto()
    SYNCED = auto()
    UNTRACKED = auto()

    def __str__(self):
        if self == FileStatus.SERVER_ONLY:
            return "Not downloaded"
        elif self == FileStatus.SERVER_COPY_OUTDATED:
            return "Local copy newer"
        elif self == FileStatus.LOCAL_COPY_OUTDATED:
            return "Lens copy newer"
        elif self == FileStatus.SYNCED:
            return "Synced"
        elif self == FileStatus.UNTRACKED:
            return "Untracked"
        else:
            logger.error(f"Unknown file status: {self}")
            return "Unknown"


class TokenRefreshThread(QThread):
    token_refreshed = Signal()

    def run(self):
        while True:
            self.token_refreshed.emit()
            self.sleep(600)


class WorkspaceModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    NameAndIsFolderRole = Qt.UserRole + 2
    IdRole = Qt.UserRole + 3
    NameStatusAndIsFolderRole = Qt.UserRole + 4
    StatusRole = Qt.UserRole + 5
    subPath = ""

    def __init__(self, workspaceDict, **kwargs):
        parent = kwargs.get("parent", None)
        super().__init__(parent)

        self.workspace = workspaceDict

        self.organizationId = workspaceDict["organizationId"]
        self._id = workspaceDict["_id"]

        self.name = workspaceDict["name"]
        self.path = CACHE_PATH + self._id
        self.subPath = kwargs.get("subPath", "")
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
        local_dirs = []
        local_files = []

        for basename in files:
            # First we filter the dirs
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
                    {"name": basename},
                )
                local_dirs.append(file_item)

        for basename in files:
            # Then we add the files
            file_path = Utils.joinPath(self.getFullPath(), basename)
            if not os.path.isdir(file_path):
                created_time = Utils.getFileCreatedAt(file_path)
                modified_time = Utils.getFileUpdatedAt(file_path)
                base, extension = os.path.splitext(basename)
                if extension.lower() != ".fcbak":
                    file_item = FileItem(
                        basename,
                        extension.lower(),
                        self.getFullPath(),
                        False,
                        [basename],
                        basename,
                        created_time,
                        modified_time,
                        FileStatus.UNTRACKED,
                    )
                    local_files.append(file_item)
        return local_dirs, local_files

    def rowCount(self, parent=None):
        return len(self.files)

    def data(self, index, role=Qt.DisplayRole):
        pass  # Implemented in subclasses

    def getWorkspacePath(self):
        """Returns the path of the workspace including subpath"""
        if self.subPath == "":
            return self.name
        else:
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

    def isEmptyDirectory(self, index):
        dirName = self.data(index, WorkspaceModel.NameRole)
        pathDir = Utils.joinPath(self.getFullPath(), dirName)
        if os.path.isdir(pathDir):
            files = os.listdir(pathDir)
            return not files or (
                len(files) == 1
                and files[0] == ".thumbnails"
                and os.path.isdir(Utils.joinPath(pathDir, files[0]))
            )
        elif os.path.isfile(pathDir):
            raise ValueError(f"{dirName} is not a directory but a file")
        else:
            # The file may be represented only on the server in which case it
            # is empty from the filesystem perspective.
            logger.debug(f"Dir {dirName} is not present locally")
            return True

    def _delete(self, index, deleteFunc, checkFunc, kind, refresh):
        # do not call refreshModel() as it may be part of a call from a subclass
        fileName = self.data(index, WorkspaceModel.NameRole)

        fileName = Utils.joinPath(self.getFullPath(), fileName)
        if os.path.exists(fileName):
            if checkFunc(fileName):
                deleteFunc(fileName)
            else:
                logger.error(f"{fileName} is not a {kind}")
        else:
            # apparently it was only represented on the server
            logger.debug(f"{fileName} is not present locally")
        if refresh:
            self.refreshModel()

    def deleteDirectory(self, index, refresh=True):
        """Delete a directory given an index."""
        self._delete(index, shutil.rmtree, os.path.isdir, "directory", refresh)

    def deleteFile(self, index, refresh=True):
        """Delete a file given an index.

        The method should not call refreshModel() as it may be combined with a
        method from a subclass.
        """
        self._delete(index, os.remove, os.path.isfile, "file", refresh)

    def sortFiles(self, dirs, files, key=lambda fileItem: fileItem.name):
        return sorted(dirs, key=key) + sorted(files, key=key)

    def getFileNames(self):
        """
        Get the filenames of the currentdirectory.
        """
        localDirs, localFiles = self.getLocalFiles()
        return [fi.name for fi in localDirs + localFiles]

    def createDir(self, dir):
        fullPath = Utils.joinPath(self.getFullPath(), dir)
        if not os.path.exists(fullPath):
            os.makedirs(fullPath)

    def dump(self):
        """
        useful for debugging.  This will return the contents in a printable form
        """

        for file in self.files:
            print(file)


class LocalWorkspaceModel(WorkspaceModel):
    def __init__(self, workspaceDict, **kwargs):
        super().__init__(workspaceDict, **kwargs)

        self.refreshModel()

    def refreshModel(self):
        self.clearModel()
        if not os.path.isdir(self.path):
            self.files = []
            return
        localDirs, localFiles = self.getLocalFiles()
        self.beginResetModel()
        self.files = self.sortFiles(localDirs, localFiles)
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
            return file_item.name, None, file_item.is_folder
        return None

    def openParentFolder(self):
        self.subPath = os.path.dirname(self.subPath)
        self.refreshModel()

    def openDirectory(self, index):
        file_item = self.files[index.row()]
        if file_item.is_folder:
            self.subPath = Utils.joinPath(self.subPath, file_item.name)
            self.refreshModel()
        else:
            logger.error(f"{file_item.name} is not a directory")


class ServerWorkspaceModel(WorkspaceModel):
    def __init__(self, workspaceDict, **kwargs):
        super().__init__(workspaceDict, **kwargs)

        # a stack of directories, the current directory is currentDirectory[-1]
        # (pushing is 'append()', popping is 'pop()')
        self.currentDirectory = [workspaceDict["rootDirectory"]]

        self.apiClient = kwargs["apiClient"]
        self.refreshModel()

        # if the folder doesnt exist, create it
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        # Create an instance of the token refresh thread
        self.refresh_thread = TokenRefreshThread()
        self.refresh_thread.token_refreshed.connect(self.refreshModel)
        self.refresh_thread.start()

    def getServerDirs(self, serverDirDicts):
        currentDir = self.currentDirectory[-1]
        serverDirs = []
        for dirDict in serverDirDicts:
            nameDir = dirDict["name"]

            file_item = FileItem(
                nameDir,
                "",
                currentDir["name"],
                True,
                "",
                "",
                "",
                "",
                "",
                dirDict,
            )
            serverDirs.append(file_item)
        return serverDirs

    def getServerDates(self, currentVersion):
        """
        Return the updated and created date given a server version

        The updatedDate may not be available in which case the createdDate is
        used.
        """
        createdDate = currentVersion["createdAt"]
        hasFileUpdatedAt = "fileUpdatedAt" in currentVersion["additionalData"]
        logger.debug(f"has fileUpdatedAt? {hasFileUpdatedAt}")
        updatedDate = currentVersion["additionalData"].get("fileUpdatedAt", createdDate)
        return updatedDate, createdDate

    def getServerFiles(self, serverFileDicts):
        serverFiles = []
        for serverFileDict in serverFileDicts:
            currentVersion = serverFileDict["currentVersion"]

            updatedDate, createdDate = VersionModel.getVersionDateTime(currentVersion)
            custFileName = serverFileDict["custFileName"]
            _, extension = os.path.splitext(custFileName)
            file_item = FileItem(
                custFileName,
                extension.lower(),
                self.getFullPath(),
                False,
                [custFileName],
                custFileName,
                createdDate,
                updatedDate,
                FileStatus.SERVER_ONLY,
                serverFileDict,
            )
            serverFiles.append(file_item)
        return serverFiles

    def mergeFiles(self, serverFiles, localFiles, funcUpdateFound, funcUpdateNotFound):
        filesToAdd = []

        # O(n^2) can be made more efficient with sorting and parallel iteration
        # for now it suffices
        for localFile in localFiles:
            # logger.debug(f'serverFile: {localFile.name}')
            for serverFile in serverFiles:
                # logger.debug(f'localFile: {serverFile.name}')
                if serverFile.name == localFile.name:
                    # logger.debug(f'found {serverFile.name} locally')
                    funcUpdateFound(serverFile, localFile)
                    break
            else:  # the server does not have this file
                # Note that this 'else' is part of the 'for and not of the 'if'
                # inside the 'for'
                funcUpdateNotFound(localFile)
                filesToAdd.append(localFile)

        return serverFiles + filesToAdd

    def refreshModel(self, firstCall=True):
        """Refresh the model in terms of file items.

        We retrieve the server files and directories, the local files and
        directories, compare them and update the model with FileItem instances
        that reflect the status of the server and local file system.

        throws an APIClientException
        """

        self.clearModel()

        currentDir = self.currentDirectory[-1]

        # retrieve the dirs and files from the server
        # the directories are shown first and then the files
        serverDirDict = self.apiClient.getDirectory(currentDir["_id"])
        serverDirs = self.getServerDirs(serverDirDict["directories"])
        serverFiles = self.getServerFiles(serverDirDict["files"])

        def updateDirFound(serverFileItem, localFileItem):
            pass

        def updateDirNotFound(fileItem):
            pass

        def updateFileFound(serverFileItem, localFileItem):
            serverDate = serverFileItem.updatedAt
            localDate = localFileItem.updatedAt
            if serverDate < localDate:
                # logger.debug(f"serverDate updated: {serverDate}")
                # logger.debug(f"serverCreated: {serverFileItem.createdAt}")
                # logger.debug(f"localDate updated: {localDate}")
                # logger.debug(f"localCreated: {localFileItem.createdAt}")
                serverFileItem.status = FileStatus.SERVER_COPY_OUTDATED
            elif serverDate > localDate:
                # logger.debug(f"serverDate updated: {serverDate}")
                # logger.debug(f"serverCreated: {serverFileItem.createdAt}")
                # logger.debug(f"localDate updated: {localDate}")
                # logger.debug(f"localCreated: {localFileItem.createdAt}")
                serverFileItem.status = FileStatus.LOCAL_COPY_OUTDATED
            else:
                serverFileItem.status = FileStatus.SYNCED

        def updateFileNotFound(localFileItem):
            localFileItem.status = FileStatus.UNTRACKED

        localDirs, localFiles = self.getLocalFiles()
        dirs = self.mergeFiles(serverDirs, localDirs, updateDirFound, updateDirNotFound)
        files = self.mergeFiles(
            serverFiles, localFiles, updateFileFound, updateFileNotFound
        )

        self.beginResetModel()
        self.files = self.sortFiles(dirs, files)
        self.endResetModel()

        # This needs to be disabled unless we maintain our own file administration.
        # If a file is deleted on the server, the addon will automatically add it to
        # the server again by means of this call.
        # if firstCall:
        #     self.uploadUntrackedFiles()

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
            # Commented out the code below.  It is confusing, and if at a later
            # stage the modelId is required, it would bet better to create a
            # role for that.
            # if (
            #     file_item.serverFileDict is not None
            #     and "modelId" in file_item.serverFileDict
            # ):
            #     return file_item.serverFileDict["modelId"]
            return file_item.serverFileDict["_id"]
        elif role == self.StatusRole:
            return file_item.status
        elif role == self.NameStatusAndIsFolderRole:
            return file_item.name, file_item.status, file_item.is_folder
        return None

    def getServerThumbnail(self, fileId):
        for file_item in self.files:
            if (
                file_item.serverFileDict is not None
                and "modelId" in file_item.serverFileDict
                and file_item.serverFileDict["modelId"] == fileId
                and "thumbnailUrlCache" in file_item.serverFileDict
            ):
                thumbnailUrl = file_item.serverFileDict["thumbnailUrlCache"]
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
                except requests.exceptions.RequestException:
                    pass  # no thumbnail online.
        return None

    def openDirectory(self, index):
        file_item = self.files[index.row()]
        self.subPath = Utils.joinPath(self.subPath, file_item.name)
        # push the directory to the stack
        if file_item.serverFileDict.get("_id"):
            # the server knows about this directory
            self.currentDirectory.append(file_item.serverFileDict)
        else:
            # the server needs to know about this directory
            id = self.createDir(file_item.name)
            self.currentDirectory.append({"_id": id, "name": file_item.name})
        self.refreshModel()

    def _isEmptyDirectoryOnServer(self, index):
        # throws an APIClientException
        fileItem = self.files[index.row()]
        if fileItem.serverFileDict and "_id" in fileItem.serverFileDict:
            dirDict = self.apiClient.getDirectory(fileItem.serverFileDict["_id"])
            return (not dirDict["files"]) and (not dirDict["directories"])
        else:
            # It may be the case that the file is only represented locally in
            # which case it is empty from the server perspective
            logger.debug(f"Dir {fileItem.name} is not present on the server")
            return True

    def isEmptyDirectory(self, index):
        # throws an APIClientException
        return super().isEmptyDirectory(index) and self._isEmptyDirectoryOnServer(index)

    def deleteDirectory(self, index):
        """Delete a directory on the server and on the local filesystem.

        It assumes that the directory is empty.  It should not call
        refreshModel because it is combined with a call to super().
        """
        super().deleteDirectory(index, NO_REFRESH)
        fileItem = self.files[index.row()]
        if fileItem.serverFileDict and "_id" in fileItem.serverFileDict:
            logger.debug(f"doing an API delete on {fileItem.name}")
            self.apiClient.deleteDirectory(fileItem.serverFileDict["_id"])
        else:
            logger.debug(f"Dir {fileItem.name} is not on the server.")
        self.refreshModel()

    def deleteFileLocally(self, index):
        """Delete a file on the local filesystem."""
        super().deleteFile(index)

    def deleteFile(self, index):
        """Delete a file from the server.

        This function assumes that the files have been removed locally.
        """
        file_item = self.files[index.row()]

        id = file_item.serverFileDict["_id"]
        modelId = file_item.serverFileDict["modelId"]
        logger.debug(f"Doing a delete on file {id} with modelId {modelId}")

        self.apiClient.deleteFile(file_item.serverFileDict["_id"])
        self.refreshModel()

    def getFileItemFileId(self, fileId):
        for fi in self.files:
            if (
                fi.serverFileDict
                and "_id" in fi.serverFileDict
                and fi.serverFileDict["_id"] == fileId
            ):
                return fi
        logger.error("Cannot find the correct fileId")
        return None

    def downloadFile(self, fileItem):
        # This will download the current (active) version.
        # Throws an APIClientException
        currentVersion = fileItem.serverFileDict["currentVersion"]
        self.downloadVersion(fileItem, currentVersion)

    def downloadVersion(self, fileItem, version):
        # This will download a specific version
        # Throws an APIClientException
        if fileItem.is_folder:
            logger.warn("Download of folders not supported yet.")
            self.refreshModel()
            return False
        else:
            logger.info(f"Downloading file {fileItem.name}")
            file_path = fileItem.getPath()
            self.apiClient.downloadFileFromServer(version["uniqueFileName"], file_path)
            updatedAt, createdAt = VersionModel.getVersionDateTime(version)
            Utils.setFileModificationTimes(file_path, updatedAt, createdAt)
            self.refreshModel()
            return True

    def uploadUntrackedFiles(self):
        # This function upload untracked files automatically to Server.
        # It is called in refreshModel (and not only into addCurrentFile and addFiles)
        # in order to also catch when user add file manually to the folder.
        # A parameter to refreshModel is added to prevent infinite loops just in case.
        refreshRequired = False
        for file_item in self.files:
            if file_item.status == FileStatus.UNTRACKED:
                logger.debug(
                    f"Upload untracked file {file_item.name} "
                    "from uploadUntrackedFiles()"
                )
                self.upload(file_item.name)
                refreshRequired = True
        if refreshRequired:
            self.refreshModel(False)

    def upload(
        self, fileName, fileId=None, message="Update from the Ondsel Lens addon"
    ):
        # unique file name is always generated even if file is already on the
        # server under another uniqueFileName.  fileId is only used for updates

        # raises APIClientException

        logger.info(f"Uploading file {fileName}")
        base, extension = os.path.splitext(fileName)
        uniqueName = f"{str(uuid.uuid4())}.fcstd"  # TODO replace .fcstd by {extension}

        file_path = Utils.joinPath(self.getFullPath(), fileName)
        fileUpdateDate = Utils.getFileUpdatedAt(file_path)

        self.apiClient.uploadFileToServer(uniqueName, file_path)

        currentDir = self.currentDirectory[-1]
        workspace = self.summarizeWorkspace()

        if fileId:
            result = self.apiClient.updateFileObj(
                fileId, fileUpdateDate, uniqueName, currentDir, workspace, message
            )
            # no longer needed
            # if extension.lower() in [".fcstd", ".obj"]:
            #     self.apiClient.regenerateModelObj(result["modelId"], fileId)
        else:
            result = self.apiClient.createFile(
                fileName,
                fileUpdateDate,
                uniqueName,
                currentDir,
                workspace,
            )
            fileId = result["_id"]
            if extension.lower() in [".fcstd", ".obj"]:
                # TODO: This creates a file in the root directory as well
                self.apiClient.createModel(fileId)

    def openParentFolder(self):
        self.subPath = os.path.dirname(self.subPath)
        self.currentDirectory.pop()
        self.refreshModel()

    def getFileNames(self):
        # raises an APIClientException
        currentDir = self.currentDirectory[-1]
        serverDirDict = self.apiClient.getDirectory(currentDir["_id"])
        return (
            super().getFileNames()
            + [itemDict["custFileName"] for itemDict in serverDirDict["files"]]
            + [itemDict["name"] for itemDict in serverDirDict["directories"]]
        )

    def summarizeWorkspace(self):
        return {k: self.workspace[k] for k in ("_id", "name", "refName", "open")}

    def createDir(self, nameDirectory):
        # raises an APIClientException
        currentDir = self.currentDirectory[-1]
        workspace = self.summarizeWorkspace()
        result = self.apiClient.createDirectory(
            nameDirectory,
            currentDir["_id"],
            currentDir["name"],
            workspace,
        )

        return result["_id"]


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
        status=FileStatus.UNTRACKED,
        serverFileDict=None,
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

    def getPath(self):
        return Utils.joinPath(self.path, self.name)

    def getModelId(self):
        if self.serverFileDict and "modelId" in self.serverFileDict:
            return self.serverFileDict["modelId"]
        else:
            return None

    def dump(self):
        print(
            cleandoc(
                f"""
                name: {self.name}
                 ext: {self.ext}
                 path: {self.path}
                 is_folder: {self.is_folder}
                 versions: {self.versions}
                 current_version: {self.current_version}
                       createdAt: {self.createdAt}
                 updatedAt: {self.updatedAt}
                 status: {self.status}
                 serverFileDict: {self.serverFileDict}"""
            )
        )
