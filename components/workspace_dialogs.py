from PySide import QtGui
from PySide.QtWidgets import QMessageBox


def confirmFileTransfer(message, transferMessage):
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Confirmation")
    msg_box.setText(f"{message} {transferMessage}\nAre you sure you want to proceed?")
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.No)

    return msg_box.exec_() == QMessageBox.Yes


def confirmDownload(message):
    return confirmFileTransfer(message, "Downloading will override this local version.")


class EnterCommitMessageDialog(QtGui.QDialog):
    MAX_LENGTH_COMMIT_MESSAGE = 50

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commit Message")

        self.label = QtGui.QLabel("Please provide a commit message:")
        self.commit_message_input = QtGui.QLineEdit()
        self.commit_message_input.setMaxLength(
            EnterCommitMessageDialog.MAX_LENGTH_COMMIT_MESSAGE
        )

        self.upload_button = QtGui.QPushButton("Upload")
        self.upload_button.clicked.connect(self.accept)

        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.upload_button.setEnabled(False)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.commit_message_input)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.upload_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Connect textChanged signals to enable/disable the create button
        self.commit_message_input.textChanged.connect(self.check_commit_message)

    def check_commit_message(self):
        commit_message = self.commit_message_input.text()
        enabled = len(commit_message) > 0
        self.upload_button.setEnabled(enabled)

    def getCommitMessage(self):
        return self.commit_message_input.text()


class CreateDirDialog(QtGui.QDialog):
    def __init__(self, filenames):
        super().__init__()
        self.setWindowTitle("Create Directory")

        self.filenames = filenames
        self.label = QtGui.QLabel("Directory name:")
        self.directory_input = QtGui.QLineEdit()

        self.create_button = QtGui.QPushButton("Create")
        self.create_button.clicked.connect(self.accept)

        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.create_button.setEnabled(False)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.directory_input)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Connect textChanged signals to enable/disable the create button
        self.directory_input.textChanged.connect(self.check_dir)

    def check_dir(self):
        dir = self.directory_input.text()
        enabled = not (dir in self.filenames or dir == "")
        self.create_button.setEnabled(enabled)

    def getDir(self):
        return self.directory_input.text()
