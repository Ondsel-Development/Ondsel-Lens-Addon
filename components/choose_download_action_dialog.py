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

        choose_open_on_web = QRadioButton("Explore on the Ondsel Lens website")
        choose_open_on_web.answer = self.OPEN_ON_WEB
        choose_open_on_web.toggled.connect(self.selection_made)

        choose_download_to_cad = QRadioButton("Show file in Ondsel ES")
        choose_download_to_cad.answer = self.DL_TO_MEM
        choose_download_to_cad.toggled.connect(self.selection_made)

        layout = QVBoxLayout()
        layout.addWidget(message)

        if conn_status == ConnStatus.CONNECTED:
            layout.addWidget(choose_open_on_web)
            layout.addWidget(choose_download_to_cad)
            button_box = self.create_button_box(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
        elif conn_status == ConnStatus.DISCONNECTED:
            offline_msg = QLabel(
                "Sorry, you are currently offline. Cannot reach Ondsel."
            )
            layout.addWidget(offline_msg)
            button_box = self.create_button_box(QDialogButtonBox.Ok)
        else:  # ConnStatus.LOGGED_OUT
            text_download_to_cad = choose_download_to_cad.text()
            choose_download_to_cad.setText(text_download_to_cad + " (offline)")
            choose_download_to_cad.setDisabled(True)
            layout.addWidget(choose_open_on_web)
            layout.addWidget(choose_download_to_cad)
            button_box = self.create_button_box(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )

        layout.addWidget(button_box)
        self.setLayout(layout)

    def create_button_box(self, buttons):
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box

    def selection_made(self):
        rb = self.sender()
        if rb.isChecked():
            self.answer = rb.answer
