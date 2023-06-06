from PySide.QtCore import Qt, QAbstractTableModel, QModelIndex
from tzlocal import get_localzone
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import datetime
import os
import threading
import time
import xml.etree.ElementTree as ET
import zipfile


class LocalVersionModelUpdater(FileSystemEventHandler):
    def __init__(self, model, directory):
        super().__init__()
        self.model = model
        self.directory = directory

    def on_deleted(self, event):
        time.sleep(0.1)
        self.model.refreshModel()

    def on_moved(self, event):
        time.sleep(0.1)
        self.model.refreshModel()


class VersionModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = ["created", "uniqueName"]
        self.sort_column = 0  # Column index for sorting
        self.sort_order = Qt.DescendingOrder  # Sort order
        self.versions = []

    def refreshModel(self):
        pass  # Implemented in subclasses

    def clearModel(self):
        self.beginResetModel()
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        self.versions = []
        self.endResetModel()

    def data(self, index, role):
        row = index.row()
        column = index.column()
        rowdata = self.versions[row]

        if role == Qt.DisplayRole:
            if column == 0:
                return rowdata["created"]
            elif column == 1:
                return rowdata["uniqueName"]

        # Additional role for accessing the full filename
        if role == Qt.UserRole:
            return rowdata["resource"]

        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self.sort_column = column
        self.sort_order = order
        self.data.sort(
            key=lambda x: x[self.sort_column],
            reverse=self.sort_order == Qt.DescendingOrder,
        )
        self.layoutChanged.emit()

    def convertTime(self, time_str):
        """
        This converts a time string to the user's local timezone using tzlocal
        and outputs it in a friendly format
        """
        # Get the user's local timezone
        user_timezone = get_localzone()

        try:
            # Convert the time string to a datetime object
            time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")

            # Convert the time to the user's local timezone
            local_time_obj = time_obj.replace(tzinfo=datetime.timezone.utc).astimezone(
                user_timezone
            )

            # Format the local time as a friendly string
            local_time_str = local_time_obj.strftime("%Y-%m-%d %H:%M:%S %Z")

            return local_time_str
        except ValueError:
            # Handle invalid time string format
            return "Invalid time format"

    def dump(self):
        """
        useful for debugging.  This will return the contents in a printable form
        """
        data = []

        for row in range(self.rowCount()):
            row_data = {}

            for column in range(self.columnCount(None)):
                index = self.index(row, column, QModelIndex())
                value = self.data(index, Qt.DisplayRole)
                header = self.headerData(column, Qt.Horizontal, Qt.DisplayRole)

                row_data[header] = value

            data.append(row_data)
            print(f"{row_data}/n")

    def addNewVersion(self, filename):
        pass  # Implemented in subclasses

    def rowCount(self, index=QModelIndex()):
        return len(self.versions)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]


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

        self.refreshModel()

        thread = threading.Thread(
            target=self.startMonitoringFileSystem, args=(self.path,)
        )
        thread.daemon = True
        thread.start()

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
                result["CreationDate"] = self.convertTime(lastModifiedDate)
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

        if not self._isBackupFile(filename):
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
        self.versions.append(version)
        self.endInsertRows()

    def startMonitoringFileSystem(self, directory):
        event_handler = LocalVersionModelUpdater(self, directory)
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


class OndselVersionModel(VersionModel):
    def __init__(self, modelId, parent=None):
        """
        expects an Ondsel modelID
        """
        super().__init__(parent)

    def refreshModel(self):
        self.clearModel()

    def addNewVersion(self, modelId):
        """
        evaluates a filename.  Adds a version if it's a backup file to the
        document file
        """
        pass
