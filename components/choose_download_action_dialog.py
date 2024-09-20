from PySide2.QtWidgets import QRadioButton
from PySide.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel
import Utils
from APIClient import ConnStatus

logger = Utils.getLogger(__name__)


class ChooseDownloadActionDialog(QDialog):
    CANCEL = 0
    OPEN_ON_WEB = 1
    DL_TO_MEM = 2

    def __init__(self, name, data_parent, parent=None):
        super().__init__(parent)
        self.quit_on_close = False
        conn_status = data_parent.api.getStatus()

        self.setWindowTitle(name)
        self.answer = self.CANCEL

        message = QLabel(f"What should we do with '{name}'?")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if conn_status == ConnStatus.CONNECTED:
            self.choose_open_on_web = QRadioButton("Explore on the Ondsel Lens website")
            self.choose_open_on_web.answer = self.OPEN_ON_WEB
            self.choose_open_on_web.toggled.connect(self.selection_made)
            self.choose_download_to_cad = QRadioButton("Show file in Ondsel ES")
            self.choose_download_to_cad.answer = self.DL_TO_MEM
            self.choose_download_to_cad.toggled.connect(self.selection_made)
            self.layout = QVBoxLayout()
            self.layout.addWidget(message)
            self.layout.addWidget(self.choose_open_on_web)
            self.layout.addWidget(self.choose_download_to_cad)
            self.layout.addWidget(self.button_box)
            self.setLayout(self.layout)
        elif conn_status == ConnStatus.DISCONNECTED:
            offline_msg = QLabel(
                "Sorry, you are currently offline. Cannot reach Ondsel."
            )
            self.layout = QVBoxLayout()
            self.layout.addWidget(message)
            self.layout.addWidget(offline_msg)
            self.layout.addWidget(self.button_box)
            self.setLayout(self.layout)
        else:  # ConnStatus.LOGGED_OUT
            self.choose_open_on_web = QRadioButton("Explore on the Ondsel Lens website")
            self.choose_open_on_web.answer = self.OPEN_ON_WEB
            self.choose_open_on_web.toggled.connect(self.selection_made)
            self.choose_download_to_cad = QRadioButton(
                "Show file in Ondsel ES (offline)"
            )
            self.choose_download_to_cad.setDisabled(True)
            self.choose_download_to_cad.answer = self.OPEN_ON_WEB # this shouldn't actually happen
            self.layout = QVBoxLayout()
            self.layout.addWidget(message)
            self.layout.addWidget(self.choose_open_on_web)
            self.layout.addWidget(self.choose_download_to_cad)
            self.layout.addWidget(self.button_box)
            self.setLayout(self.layout)

    def selection_made(self):
        rb = self.sender()
        if rb.isChecked():
            self.answer = rb.answer
