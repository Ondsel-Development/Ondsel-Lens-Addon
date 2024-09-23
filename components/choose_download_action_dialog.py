from PySide2.QtWidgets import QRadioButton
from PySide.QtWidgets import (
    QDialog,
    QButtonGroup,
    QDialogButtonBox,
    QVBoxLayout,
    QLabel,
)
import Utils
from APIClient import ConnStatus

logger = Utils.getLogger(__name__)


class ChooseDownloadActionDialog(QDialog):
    CANCEL = 0
    DL_TO_MEM = 1
    OPEN_ON_WEB = 2

    TO_STRING_DOWNLOAD_ACTIONS = {
        DL_TO_MEM: "showInOndselES",
        OPEN_ON_WEB: "openOnWeb",
    }
    FROM_STRING_DOWNLOAD_ACTIONS = {v: k for k, v in TO_STRING_DOWNLOAD_ACTIONS.items()}

    PREF_DOWNLOAD_ACTION = "downloadAction"

    def __init__(self, name, data_parent, parent=None):
        super().__init__(parent)
        self.quit_on_close = False
        conn_status = data_parent.api.getStatus()

        self.setWindowTitle(name)
        self.answer = self.CANCEL

        message = QLabel(f"What should we do with '{name}'?")

        choose_download_to_mem = QRadioButton("Show file in Ondsel ES")
        choose_open_on_web = QRadioButton("Explore on the Ondsel Lens website")
        self.radio_button_group = QButtonGroup(self)
        self.radio_button_group.addButton(choose_download_to_mem, self.DL_TO_MEM)
        self.radio_button_group.addButton(choose_open_on_web, self.OPEN_ON_WEB)
        self.check_radio_button(choose_download_to_mem, choose_open_on_web)

        layout = QVBoxLayout()
        layout.addWidget(message)

        if conn_status == ConnStatus.CONNECTED:
            layout.addWidget(choose_download_to_mem)
            layout.addWidget(choose_open_on_web)
            ok_button_box = self.create_button_box(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
        elif conn_status == ConnStatus.DISCONNECTED:
            offline_msg = QLabel(
                "Sorry, you are currently offline. Cannot reach Ondsel."
            )
            layout.addWidget(offline_msg)
            ok_button_box = self.create_button_box(QDialogButtonBox.Ok)
        else:  # ConnStatus.LOGGED_OUT
            text_download_to_mem = choose_download_to_mem.text()
            choose_download_to_mem.setText(text_download_to_mem + " (logged out)")
            choose_download_to_mem.setDisabled(True)
            choose_download_to_mem.setChecked(False)
            choose_open_on_web.setChecked(True)
            layout.addWidget(choose_download_to_mem)
            layout.addWidget(choose_open_on_web)
            ok_button_box = self.create_button_box(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )

        layout.addWidget(ok_button_box)
        self.setLayout(layout)

    def check_radio_button(self, choose_download_to_mem, choose_open_on_web):
        param_group = Utils.get_param_group()
        download_action = self.FROM_STRING_DOWNLOAD_ACTIONS.get(
            param_group.GetString(self.PREF_DOWNLOAD_ACTION), self.CANCEL
        )

        if download_action == self.DL_TO_MEM:
            choose_download_to_mem.setChecked(True)
        elif download_action == self.OPEN_ON_WEB:
            choose_open_on_web.setChecked(True)
        else:
            choose_download_to_mem.setChecked(True)

    def accept(self):
        self.answer = self.radio_button_group.checkedId()
        param_group = Utils.get_param_group()
        param_group.SetString(
            self.PREF_DOWNLOAD_ACTION, self.TO_STRING_DOWNLOAD_ACTIONS[self.answer]
        )
        super().accept()

    def create_button_box(self, buttons):
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box
