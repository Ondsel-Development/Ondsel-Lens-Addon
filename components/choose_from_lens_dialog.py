from PySide import QtWidgets
from PySide.QtWidgets import (
    QPushButton,
    QDialog,
    QButtonGroup,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
)
import Utils
from APIClient import ConnStatus

logger = Utils.getLogger(__name__)


class ChooseFromLensDialog(QDialog):
    CANCEL = 0
    CHOSEN = 1

    SELECT_FILE_ONLY = 0

    def __init__(self, name, workspaces, data_parent, parent=None):
        super().__init__(parent)
        self.quit_on_close = False
        conn_status = data_parent.api.getStatus()
        self.setWindowTitle(name)
        self.create_explore_table()
        self.create_workspaces_table(workspaces)
        self.create_button_box()
        self.answer = {
            "workspace_id": None,
            "directory_id": None,
            "file_id": None,
        }

        center_layout = QHBoxLayout()
        center_layout.addWidget(self.workspaces_table)
        center_layout.addWidget(self.explore_table)
        overall_layout = QVBoxLayout()
        overall_layout.addLayout(center_layout)
        overall_layout.addWidget(self.button_box)

        self.setLayout(overall_layout)

    def create_explore_table(self):
        self.explore_table = QtWidgets.QTableWidget(0, 3)
        self.explore_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.explore_table.setHorizontalHeaderLabels(("", "Name", "Type"))
        self.explore_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )
        self.explore_table.verticalHeader().hide()
        self.explore_table.setShowGrid(False)
        # self.filesTable.cellActivated.connect(self.openFileOfItem)

    def create_workspaces_table(self, workspaces):
        if workspaces is None:
            self.workspaces = []  # TODO: populate with user's entries
        else:
            self.workspaces = workspaces
        self.workspaces_table = QtWidgets.QTableWidget(0, 1)
        self.workspaces_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.workspaces_table.setHorizontalHeaderLabels(("Workspaces",))
        self.workspaces_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        self.workspaces_table.verticalHeader().hide()
        self.workspaces_table.setShowGrid(False)

        for ws in self.workspaces:
            ws_desc = f"{ws['owner']} | {ws['name']}"
            row = self.workspaces_table.rowCount()
            self.workspaces_table.insertRow(row)
            self.workspaces_table.setItem(row, 0, QtWidgets.QTableWidgetItem(ws_desc))

    def create_button_box(self):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.addButton(QDialogButtonBox.Open)
        self.button_box.accepted.connect(self.accept)

    def accept(self):
        print("here")
        super().accept()
