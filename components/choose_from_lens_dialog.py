from APIClient import APICallResult
from PySide import QtWidgets, QtGui
from PySide import QtCore
from PySide.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
)
import Utils
from components.QTableWidgetWithKbReturnSupport import QTableWidgetWithKbReturnSupport
from models.directory import Directory
from models.directory_summary import DirectorySummary
from models.file_summary import FileSummary

logger = Utils.getLogger(__name__)


class ChooseFromLensDialog(QDialog):
    CANCEL = 0
    CHOSEN = 1

    SELECT_FILE_ONLY = 0

    folder_icon = QtGui.QIcon(Utils.icon_path + "folder.svg")
    document_icon = QtGui.QIcon(Utils.icon_path + "file-outline.svg")

    def __init__(self, name, workspace_ids, data_parent, parent=None):
        super().__init__(parent)
        self.quit_on_close = False
        self.api = data_parent.api
        conn_status = self.api.getStatus()
        self.setWindowTitle(name)
        #
        self.directory_stack = []
        self.answer = {
            "workspace": None,
            "directory": None,
            "file": None,
        }
        # location at top
        self.location_label = QLabel("location goes here")
        # buttons on bottom
        self.create_button_box()
        # workspaces pane (on the left)
        self.workspaces_table = QTableWidgetWithKbReturnSupport(0, 1)
        self.current_workspace_index = 0
        self.workspace_items = []
        self.create_workspaces_table(workspace_ids)
        # explore pane (on the right)
        self.current_directory = None
        self.explore_table = QTableWidgetWithKbReturnSupport(0, 3)
        self.current_explore_index = None
        self.explore_items = []
        self.create_explore_table()
        self.populate_root_dir_in_explore_pane()
        #
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.workspaces_table, stretch=1)
        center_layout.addWidget(self.explore_table, stretch=3)
        overall_layout = QVBoxLayout()
        overall_layout.addWidget(self.location_label)
        overall_layout.addLayout(center_layout)
        overall_layout.addWidget(self.button_box)
        self.setLayout(overall_layout)

    def current_workspace(self):
        return self.workspace_items[self.current_workspace_index]

    def current_explore_item(self):
        if self.current_explore_index is not None:
            return self.explore_items[self.current_explore_index]
        return None

    def create_explore_table(self):
        self.explore_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.explore_table.setHorizontalHeaderLabels(("", "Name", "Type"))
        self.explore_table.horizontalHeader().resizeSection(0, 8)
        self.explore_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )
        self.explore_table.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeToContents
        )
        self.explore_table.verticalHeader().hide()
        self.explore_table.setShowGrid(False)
        self.explore_table.cellClicked.connect(self.highlighted_explore_pane_cell)
        self.explore_table.itemDoubleClicked.connect(self.chosen_explore_pane_item)

    def populate_root_dir_in_explore_pane(self):
        """
        For the given workspace selected, refresh the contents of the explore pane.
        This function is run during init and any time a new workspace is selected.
        """
        workspace = self.current_workspace()
        directorySummary = workspace.rootDirectory
        self.explore_table.setRowCount(0)  # wipes the current entries out
        dir, resp = self.api.fancy_auth_call(
            self.api.get_directory_including_public, directorySummary._id
        )
        if resp != APICallResult.OK:  # a problem _shouldn't_ happen at this point
            logger.warn(
                f"connection problem: {resp} on directory {directorySummary._id}"
            )
            return
        self.directory_stack = [dir]
        self.current_directory = dir
        self.explore_items = []
        self._extend_explore_pane_with_directory(dir)
        self.current_explore_index = None
        self.refreshLocation()
        self.btn_open.setDisabled(True)

    def _extend_explore_pane_with_directory(self, dir):
        for d in dir.directories:
            row = self.explore_table.rowCount()
            self.explore_table.insertRow(row)
            folder_icon = QtWidgets.QTableWidgetItem()
            folder_icon.setIcon(self.folder_icon)
            self.explore_table.setItem(row, 0, folder_icon)
            self.explore_table.setItem(row, 1, QtWidgets.QTableWidgetItem(d.name))
            self.explore_table.setItem(row, 2, QtWidgets.QTableWidgetItem("Folder"))
            self.explore_items.append(d)
        for f in dir.files:
            row = self.explore_table.rowCount()
            self.explore_table.insertRow(row)
            document_icon = QtWidgets.QTableWidgetItem()
            document_icon.setIcon(self.document_icon)
            self.explore_table.setItem(row, 0, document_icon)
            self.explore_table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(f.custFileName)
            )
            ext = f.custFileName.split(".")[-1]
            if len(ext) == len(f.custFileName):
                type_name = "File"
            else:
                type_name = f"{ext} File"
            self.explore_table.setItem(row, 2, QtWidgets.QTableWidgetItem(type_name))
            self.explore_items.append(f)

    def _append_back_folder(self, parent_directory: DirectorySummary):
        row = self.explore_table.rowCount()
        self.explore_table.insertRow(row)
        folder_icon = QtWidgets.QTableWidgetItem()
        folder_icon.setIcon(self.folder_icon)
        self.explore_table.setItem(0, 0, folder_icon)
        self.explore_table.setItem(0, 1, QtWidgets.QTableWidgetItem(".."))
        self.explore_table.setItem(0, 2, QtWidgets.QTableWidgetItem(""))
        self.explore_items.append(parent_directory)

    def open_directory_in_explore_pane(self, directory_summary):
        self.explore_table.setRowCount(0)  # wipes the current entries out
        dir, resp = self.api.fancy_auth_call(
            self.api.get_directory_including_public, directory_summary._id
        )
        if resp != APICallResult.OK:  # a problem _shouldn't_ happen at this point
            logger.warn(
                f"connection problem: {resp} on directory {directory_summary._id}"
            )
            return
        self.directory_stack.append(directory_summary)  # stack grows
        self.current_directory = dir
        self.explore_items = []
        self._append_back_folder(directory_summary)
        self._extend_explore_pane_with_directory(dir)
        self.current_explore_index = None
        self.refreshLocation()
        self.btn_open.setDisabled(True)

    def restore_parent_directory_in_explore_pane(self):
        self.explore_table.setRowCount(0)  # wipes the current entries out
        _ = self.directory_stack.pop()  # stack shrinks
        directory_summary = self.directory_stack[-1]
        dir, resp = self.api.fancy_auth_call(
            self.api.get_directory_including_public, directory_summary._id
        )
        if resp != APICallResult.OK:  # a problem _shouldn't_ happen at this point
            logger.warn(
                f"connection problem: {resp} on directory {directory_summary._id}"
            )
            return
        self.current_directory = dir
        self.explore_items = []
        if len(self.directory_stack) >= 2:
            self._append_back_folder(directory_summary)
        self._extend_explore_pane_with_directory(dir)
        self.current_explore_index = None
        self.refreshLocation()
        self.btn_open.setDisabled(True)

    def create_workspaces_table(self, workspace_ids):
        """populates the workspaces pane. this function is only designed to be run once at startup"""
        self.workspace_items = []
        for id in workspace_ids:
            ws, resp = self.api.fancy_auth_call(
                self.api.get_workspace_including_public, id
            )
            if resp != APICallResult.OK:  # a problem _shouldn't_ happen at this point
                logger.warn(f"connection problem: {resp} on workspace {id}")
                return
            self.workspace_items.append(ws)
        self.workspaces_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.workspaces_table.setHorizontalHeaderLabels(("Workspaces",))
        self.workspaces_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        self.workspaces_table.verticalHeader().hide()
        self.workspaces_table.setShowGrid(False)
        for ws in self.workspace_items:
            ws_desc = f"{ws.describe_owner()} | {ws.name}"
            row = self.workspaces_table.rowCount()
            self.workspaces_table.insertRow(row)
            self.workspaces_table.setItem(row, 0, QtWidgets.QTableWidgetItem(ws_desc))
        self.current_workspace_index = 0
        self.workspaces_table.cellClicked.connect(self.highlighted_workspace_pane_cell)

    def create_button_box(self):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.addButton(QDialogButtonBox.Open)
        self.button_box.accepted.connect(self.okay)
        self.button_box.rejected.connect(self.cancel)
        self.btn_open = self.button_box.button(QDialogButtonBox.Open)
        self.btn_open.setDisabled(True)

    def okay(self):
        self.answer["workspace"] = self.current_workspace()
        self.answer["directory"] = self.current_directory
        self.answer["file"] = self.current_explore_item()
        super().accept()

    def cancel(self):
        super().reject()

    def refreshLocation(self):
        ws = self.current_workspace()
        item = self.current_explore_item()
        route_name = ws.generic_prefix_name()
        dir_path = "/"
        if len(self.directory_stack) > 1:
            dir_path += "/".join([d.name for d in self.directory_stack[1:]]) + "/"
        if item is None:
            text = f"{route_name}{dir_path}"
        elif isinstance(item, FileSummary):
            text = f"{route_name}{dir_path}{item.custFileName}"
        else:
            if self.directory_is_back_indicator(item):
                text = f"{route_name}{dir_path}"
            else:
                text = f"{route_name}{dir_path}{item.name}/"
        self.location_label.setText(text)

    def directory_is_back_indicator(self, dir):
        back = False  # going down INTO the directory tree
        if len(self.directory_stack) >= 2:
            own_dir = self.directory_stack[-1]
            if (
                dir._id == own_dir._id
            ):  # if you are "going" to the last directory, that is a flag-of-exit
                back = True  # exiting OUT of the directory tree
        return back

    def highlighted_explore_pane_cell(self, row, _column):
        self.current_explore_index = row
        item = self.current_explore_item()
        if item is None:
            self.btn_open.setDisabled(True)
        elif isinstance(item, FileSummary):
            self.btn_open.setDisabled(False)
        else:
            self.btn_open.setDisabled(True)
        self.refreshLocation()

    def chosen_explore_pane_item(self, target):
        self.current_explore_index = target.row()
        item = self.current_explore_item()
        if isinstance(item, FileSummary):
            return self.okay()
        if isinstance(item, DirectorySummary):
            if self.directory_is_back_indicator(item):
                self.restore_parent_directory_in_explore_pane()
            else:
                self.open_directory_in_explore_pane(item)
        self.btn_open.setDisabled(True)
        self.refreshLocation()

    def highlighted_workspace_pane_cell(self, row, _column):
        self.current_workspace_index = row
        self.populate_root_dir_in_explore_pane()  # this resets most things in explore pane
