from PySide2.QtWidgets import QRadioButton

from PySide.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class ChooseDownloadActionDialog(QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.quit_on_close = False

        self.setWindowTitle(name)
        self.answer = 0  # 0 = cancel, 1 = open web, 2 = download to memory

        message = QLabel(f"What should we do with '{name}'?")

        self.choose_open_on_web = QRadioButton("Explore on Ondsel Website")
        self.choose_open_on_web.answer = 1
        self.choose_open_on_web.toggled.connect(self.selection_made)
        self.choose_download_to_cad = QRadioButton("Download file to CAD")
        self.choose_download_to_cad.answer = 2
        self.choose_download_to_cad.toggled.connect(self.selection_made)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

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
