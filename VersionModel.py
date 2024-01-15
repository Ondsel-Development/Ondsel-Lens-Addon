# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

from PySide.QtCore import Qt, QAbstractListModel, QModelIndex, QFileSystemWatcher
from tzlocal import get_localzone
import datetime
import os
import xml.etree.ElementTree as ET
import zipfile

import Utils

logger = Utils.getLogger(__name__)


CONVERT_TO_LOCAL_TZ = True


class VersionModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.versions = []

    @staticmethod
    def getVersionDateTime(version):
        """
        Return the updated and created date given a server version

        The updatedDate may not be available in which case the createdDate is
        used.
        """
        createdDate = version["createdAt"]
        updatedDate = version["additionalData"].get("fileUpdatedAt", createdDate)
        return updatedDate, createdDate

    def refreshModel(self):
        pass  # Implemented in subclasses

    def clearModel(self):
        self.beginResetModel()
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        self.versions = []
        self.endResetModel()

    def data(self, index, role):
        pass  # Implemented in subclasses

    def convertTime(self, time, convertToLocalTZ=False):
        """
        This converts a time string to the user's local timezone using tzlocal
        and outputs it in a friendly format
        """
        # Get the user's local timezone
        user_timezone = get_localzone()

        try:
            # Convert the time string to a datetime object
            if isinstance(time, int):
                time_obj = datetime.datetime.fromtimestamp(time)
            else:
                time_obj = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")

            if convertToLocalTZ:
                # Convert the time to the user's local timezone
                time_obj = time_obj.replace(tzinfo=datetime.timezone.utc).astimezone(
                    user_timezone
                )

            # Format the local time as a friendly string
            time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S")

            return time_str
        except ValueError:
            # Handle invalid time string format
            return "Invalid time format"

    def dump(self):
        """
        useful for debugging.  This will return the contents in a printable form
        """
        data = []

        for row in range(self.rowCount()):
            index = self.index(row, QModelIndex())
            value = self.data(index, Qt.DisplayRole)

            data.append(value)
            print(data)

    def addNewVersion(self, filename):
        pass  # Implemented in subclasses

    def rowCount(self, index=QModelIndex()):
        return len(self.versions)


class LocalVersionModel(VersionModel):
    def __init__(self, filename, parent=None):
        """
        expects a filename ending in .FCStd.
        """

        super().__init__(parent)
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"The specified file: {filename} doesn't exist")

        self.filename = filename
        self.path = os.path.dirname(self.filename)
        file = os.path.basename(self.filename)
        base, extension = os.path.splitext(file)

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.refreshModel)
        self.watcher.directoryChanged.connect(self.refreshModel)
        self.watcher.addPath(self.path)

        self.refreshModel()

    def refreshModel(self):
        self.clearModel()

        for fname in os.listdir(self.path):
            self.addNewVersion(fname)

    def _getFCFileInfo(self, filename):
        """
        Extracts the CreationDate from the Document.xml so we aren't
        relying on filesystem.
        Also returns the FreeCAD version used to create the file.
        """
        result = {}

        # Open the ZIP file
        with zipfile.ZipFile(filename, "r") as zip_ref:
            # Extract the Document.xml file from the ZIP
            with zip_ref.open("Document.xml") as xml_file:
                # Read the XML content
                xml_content = xml_file.read()

                # Parse the XML
                root = ET.fromstring(xml_content)

                # Extract CreationDate and ProgramVersion values
                lastModifiedDate = root.find(
                    ".//Property[@name='LastModifiedDate']/String"
                ).get("value")
                program_version = root.get("ProgramVersion")

                # Add the values to the result dictionary
                result["CreationDate"] = self.convertTime(
                    lastModifiedDate, CONVERT_TO_LOCAL_TZ
                )
                result["ProgramVersion"] = program_version

        return result

    def _isBackupFile(self, candidate):
        """
        returns a boolean whether the filename represents a backup of the model
        filename
        """

        base, extension = os.path.splitext(os.path.basename(self.filename))
        candidatebase, candidateext = os.path.splitext(os.path.basename(candidate))

        if base not in candidatebase:
            return False
        if not (
            ("FCBak" in candidateext)
            or ("FCStd" in candidateext and candidateext[-1].isdigit())
        ):
            return False

        return True

    def addNewVersion(self, filename):
        """
        evaluates a filename.  Adds a version if it's a backup file to the
        document file
        """

        if not self._isBackupFile(filename) and filename != os.path.basename(
            self.filename
        ):
            return

        resource = f"{self.path}/{filename}"
        fileInfo = self._getFCFileInfo(resource)
        version = {
            "created": fileInfo["CreationDate"],
            "uniqueName": filename,
            "resource": resource,
        }

        row = len(self.versions)

        # Add the new item to the versions list
        self.beginInsertRows(QModelIndex(), row, row)
        self.versions.insert(0, version)
        self.endInsertRows()

    def data(self, index, role):
        row = index.row()
        version = self.versions[row]

        if role == Qt.DisplayRole:
            return version["created"]
            # return version["uniqueName"]

        # Additional role for accessing the full filename
        if role == Qt.UserRole:
            return version["resource"]

        return None


class OndselVersionModel(VersionModel):
    def __init__(self, model_id, apiClient, fileItem, parent=None):
        super().__init__(parent)
        self.model_id = model_id
        self.apiClient = apiClient
        # The version model belongs to a specific fileId
        self.fileItem = fileItem

        # the version that is on disk
        self.onDiskVersionId = None

        self.refreshModel(fileItem)

    # def sortVersions(self, fileDict):
    #     """Sort the versions"

    #     The versions acquired from the API are reversed and the currentVersion
    #     (the active one is set to be the top one.
    #     """
    #     currentVersionId = fileDict['currentVersionId']
    #     versions = fileDict["versions"][::-1]
    #     indexCurrentVersionId = [v["_id"] for v in versions].index(currentVersionId)
    #     versions[indexCurrentVersionId], versions[0] = \
    #         versions[0], versions[indexCurrentVersionId]
    #     return versions

    def getOnDiskVersionId(self, fileItem):
        """Retrieve the id of a version of a file if it is on disk.

        This code checks whether a file on disk is a specific version by
        checking the updated times.  If a file on disk is indeed a specific
        version on the server we return the versionId, otherwise None.
        """
        path = fileItem.getPath()
        if os.path.isfile(path):
            updatedAtDisk = Utils.getFileUpdatedAt(path)
            for version in self.versions:
                updatedAt, createdAt = VersionModel.getVersionDateTime(version)
                if updatedAt == updatedAtDisk or createdAt == updatedAtDisk:
                    return version["_id"]
        return None

    def refreshModel(self, fileItem):
        # raises an APIClientException
        self.clearModel()
        model = self.apiClient.getModel(self.model_id)
        fileDict = model["file"]

        self.beginResetModel()
        self.versions = fileDict["versions"][::-1]
        self.namesUsers = {
            user["_id"]: user["name"] for user in fileDict["relatedUserDetails"]
        }

        # The version that is active on the server
        self.currentVersionId = fileDict["currentVersionId"]

        self.onDiskVersionId = self.getOnDiskVersionId(fileItem)
        self.endResetModel()

    def canBeMadeActive(self):
        """Whether the version on disk can be made active"""
        return (
            self.onDiskVersionId is not None
            and self.onDiskVersionId != self.currentVersionId
        )

    def getCurrentVersionId(self):
        """Get the current version.

        In this context, the current version is the one on disk and if there is
        no file on disk, it is the active version on the server.
        """
        versionId = self.currentVersionId
        if self.onDiskVersionId:
            versionId = self.onDiskVersionId
        return versionId

    def getCurrentIndex(self):
        """Get the index of the current version.

        In this context, the current version is the one on disk and if there is
        no file on disk, it is the active version on the server.
        """
        versionId = self.getCurrentVersionId()
        return [v["_id"] for v in self.versions].index(versionId)

    def getFileId(self):
        "Get the file id of the versions"
        return self.fileItem.serverFileDict["_id"]

    def data(self, index, role):
        row = index.row()
        version = self.versions[row]

        if role == Qt.DisplayRole:
            return (self.convertTime(version["createdAt"] // 1000)) + (
                " ✔️" if version["_id"] == self.currentVersionId else ""
            )
        elif role == Qt.ToolTipRole:
            nameUser = self.namesUsers.get(version["userId"])
            if nameUser:
                nameUser = f" - {nameUser}"
            else:
                nameUser = ""
            return f"{version['message']}{nameUser}"
        elif role == Qt.UserRole:
            # Additional role for accessing the unique filename and the version Id
            return version

        return None
