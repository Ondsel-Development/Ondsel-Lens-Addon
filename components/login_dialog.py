import re

from PySide.QtWidgets import QSizePolicy
from PySide import QtGui


class LoginDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        self.email_label = QtGui.QLabel("Email:")
        self.email_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.email_input = QtGui.QLineEdit()
        self.email_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.password_label = QtGui.QLabel("Password:")
        self.password_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.password_input = QtGui.QLineEdit()
        self.password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_input.setEchoMode(QtGui.QLineEdit.Password)

        self.login_button = QtGui.QPushButton("Login")
        self.login_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.login_button.clicked.connect(self.login)
        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cancel_button.clicked.connect(self.reject)

        self.login_button.setEnabled(False)

        formLayout = QtGui.QFormLayout()
        formLayout.setSpacing(5)
        formLayout.addRow(self.email_label, self.email_input)
        formLayout.addRow(self.password_label, self.password_input)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.login_button)
        buttonLayout.addWidget(self.cancel_button)

        layout.addLayout(formLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        self.adjustSize()

        # Connect textChanged signals to enable/disable login button
        self.email_input.textChanged.connect(self.check_credentials)
        self.password_input.textChanged.connect(self.check_credentials)

    def check_credentials(self):
        email = self.email_input.text()
        password = self.password_input.text()
        valid_credentials = self.validate_credentials(email, password)
        self.login_button.setEnabled(valid_credentials)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        # Perform login validation and authentication here
        if self.validate_credentials(email, password):
            self.accept()
        else:
            self.show_error_message("Invalid credentials")

    def validate_credentials(self, email, password):
        # Check if email is a valid email address using a simple regular expression
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        # Check if a password has been entered
        if not password:
            return False
        # Add additional validation logic here if needed
        # Example: Check against a user database or external authentication service

        return True  # Return True if credentials are valid, False otherwise

    def show_error_message(self, message):
        # Add code to display an error message dialog to the user
        # You can use QMessageBox or your own custom dialog implementation
        pass

    def get_credentials(self):
        email = self.email_input.text()
        password = self.password_input.text()
        return email, password
