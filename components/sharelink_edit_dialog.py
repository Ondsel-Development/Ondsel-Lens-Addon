import math
import random

import FreeCADGui

import Utils
from PySide import QtGui

PROTECTION_COMBO_BOX_LISTED = 0
PROTECTION_COMBO_BOX_UNLISTED = 1
PROTECTION_COMBO_BOX_PIN = 2
VERSION_FOLLOWING_COMBO_BOX_LOCKED = 0
VERSION_FOLLOWING_COMBO_BOX_ACTIVE = 1


class SharingLinkEditDialog(QtGui.QDialog):
    def __init__(self, linkProperties=None, parent=None):
        super(SharingLinkEditDialog, self).__init__(parent)

        # Load the UI from the .ui file
        self.dialog = FreeCADGui.PySideUic.loadUi(
            Utils.mod_path + "/SharingLinkEditDialog.ui"
        )

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.dialog)
        self.setLayout(layout)

        self.dialog.okBtn.clicked.connect(self.accept)
        self.dialog.cancelBtn.clicked.connect(self.reject)
        self.dialog.protectionComboBox.currentIndexChanged.connect(
            self.protection_changed
        )
        self.dialog.versionFollowingComboBox.currentIndexChanged.connect(
            self.version_following_changed
        )

        if linkProperties is None:
            self.linkProperties = {
                "isActive": True,
                "isSystemGenerated": False,
                "title": "",
                "description": "",
                "protection": "Listed",
                "pin": "",
                "versionFollowing": "Locked",
                "canViewModelAttributes": True,
                "canUpdateModel": True,
                "canExportFCStd": True,
                "canExportSTEP": True,
                "canExportSTL": True,
                "canExportOBJ": True,
                "isActive": True,
                "canViewModel": True,
                "canDownloadDefaultModel": True,
            }
            self.creationAction = True  # we are creating a new share link
        else:
            self.linkProperties = linkProperties
            self.creationAction = False  # we are editing an existing share link

        if self.creationAction:
            self.setWindowTitle("Create ShareLink")
            self.dialog.enabledCheckBox.setVisible(False)
        else:
            self.setWindowTitle("Edit ShareLink")
            # once created, you can NEVER change versionFollowing or protection
            self.dialog.versionFollowingComboBox.setEnabled(False)
            self.dialog.protectionComboBox.setEnabled(False)
        if self.linkProperties["isSystemGenerated"]:
            # cannot enable/disable a sys generated link
            self.dialog.enabledCheckBox.setEnabled(False)
        self.setLinkProperties()
        self.protection_changed()  # do this to set initial PIN edit visibility
        self.version_following_changed()

    def protection_changed(self):
        protectionIndex = self.dialog.protectionComboBox.currentIndex()
        if protectionIndex == PROTECTION_COMBO_BOX_PIN:
            if self.dialog.pinLineEdit.text() == "":
                random_str = ""
                for i in range(6):
                    new_digit = math.floor(random.random() * 10)
                    random_str += str(new_digit)
                self.dialog.pinLineEdit.setText(random_str)
            self.dialog.pinLabel.setVisible(True)
            self.dialog.pinLineEdit.setVisible(True)
        else:
            self.dialog.pinLabel.setVisible(False)
            self.dialog.pinLineEdit.setVisible(False)

    def version_following_changed(self):
        vfIndex = self.dialog.versionFollowingComboBox.currentIndex()
        if vfIndex == VERSION_FOLLOWING_COMBO_BOX_ACTIVE:
            self.dialog.canExportFCStdCheckBox.setChecked(False)
            self.dialog.canExportFCStdCheckBox.setEnabled(False)
            self.dialog.canExportSTEPCheckBox.setChecked(False)
            self.dialog.canExportSTEPCheckBox.setEnabled(False)
            self.dialog.canExportSTLCheckBox.setChecked(False)
            self.dialog.canExportSTLCheckBox.setEnabled(False)
            self.dialog.canExportOBJCheckBox.setChecked(False)
            self.dialog.canExportOBJCheckBox.setEnabled(False)
            self.dialog.canUpdateModelAttributesCheckBox.setChecked(False)
            self.dialog.canUpdateModelAttributesCheckBox.setEnabled(False)
        else:
            self.dialog.canExportFCStdCheckBox.setEnabled(True)
            self.dialog.canExportSTEPCheckBox.setEnabled(True)
            self.dialog.canExportSTLCheckBox.setEnabled(True)
            self.dialog.canExportOBJCheckBox.setEnabled(True)
            self.dialog.canUpdateModelAttributesCheckBox.setEnabled(True)

    def setLinkProperties(self):
        self.dialog.linkTitle.setText(self.linkProperties["title"])
        self.dialog.linkName.setText(self.linkProperties["description"])
        if self.linkProperties["protection"] == "Listed":
            self.dialog.protectionComboBox.setCurrentIndex(PROTECTION_COMBO_BOX_LISTED)
        elif self.linkProperties["protection"] == "Unlisted":
            self.dialog.protectionComboBox.setCurrentIndex(
                PROTECTION_COMBO_BOX_UNLISTED
            )
        elif self.linkProperties["protection"] == "Pin":
            self.dialog.protectionComboBox.setCurrentIndex(PROTECTION_COMBO_BOX_PIN)
        self.dialog.pinLineEdit.setText(self.linkProperties["pin"])
        if self.linkProperties["versionFollowing"] == "Locked":
            self.dialog.versionFollowingComboBox.setCurrentIndex(
                VERSION_FOLLOWING_COMBO_BOX_LOCKED
            )
        elif self.linkProperties["versionFollowing"] == "Active":
            self.dialog.versionFollowingComboBox.setCurrentIndex(
                VERSION_FOLLOWING_COMBO_BOX_ACTIVE
            )
        self.dialog.canViewModelCheckBox.setChecked(self.linkProperties["canViewModel"])
        self.dialog.canViewModelAttributesCheckBox.setChecked(
            self.linkProperties["canViewModelAttributes"]
        )
        self.dialog.canUpdateModelAttributesCheckBox.setChecked(
            self.linkProperties["canUpdateModel"]
        )
        self.dialog.canDownloadOriginalCheckBox.setChecked(
            self.linkProperties["canDownloadDefaultModel"]
        )
        self.dialog.canExportFCStdCheckBox.setChecked(
            self.linkProperties["canExportFCStd"]
        )
        self.dialog.canExportSTEPCheckBox.setChecked(
            self.linkProperties["canExportSTEP"]
        )
        self.dialog.canExportSTLCheckBox.setChecked(self.linkProperties["canExportSTL"])
        self.dialog.canExportOBJCheckBox.setChecked(self.linkProperties["canExportOBJ"])
        self.dialog.enabledCheckBox.setChecked(self.linkProperties["isActive"])

    def getLinkProperties(self):
        self.linkProperties["title"] = self.dialog.linkTitle.text()
        self.linkProperties["description"] = self.dialog.linkName.text()
        protectionIndex = self.dialog.protectionComboBox.currentIndex()
        if protectionIndex == PROTECTION_COMBO_BOX_UNLISTED:
            self.linkProperties["protection"] = "Unlisted"
            self.linkProperties["pin"] = ""
        elif protectionIndex == PROTECTION_COMBO_BOX_PIN:
            self.linkProperties["protection"] = "Pin"
            self.linkProperties["pin"] = self.dialog.pinLineEdit.text()
        else:
            self.linkProperties["protection"] = "Listed"  # the default
            self.linkProperties["pin"] = ""
        versionFollowingIndex = self.dialog.versionFollowingComboBox.currentIndex()
        if versionFollowingIndex == VERSION_FOLLOWING_COMBO_BOX_ACTIVE:
            self.linkProperties["versionFollowing"] = "Active"
        else:
            self.linkProperties["versionFollowing"] = "Locked"  # the default
        self.linkProperties["canViewModel"] = (
            self.dialog.canViewModelCheckBox.isChecked()
        )
        self.linkProperties["canViewModelAttributes"] = (
            self.dialog.canViewModelAttributesCheckBox.isChecked()
        )
        self.linkProperties["canUpdateModel"] = (
            self.dialog.canUpdateModelAttributesCheckBox.isChecked()
        )
        self.linkProperties["canExportFCStd"] = (
            self.dialog.canExportFCStdCheckBox.isChecked()
        )
        self.linkProperties["canExportSTEP"] = (
            self.dialog.canExportSTEPCheckBox.isChecked()
        )
        self.linkProperties["canExportSTL"] = (
            self.dialog.canExportSTLCheckBox.isChecked()
        )
        self.linkProperties["canExportOBJ"] = (
            self.dialog.canExportOBJCheckBox.isChecked()
        )
        self.linkProperties["canDownloadDefaultModel"] = (
            self.dialog.canDownloadOriginalCheckBox.isChecked()
        )
        self.linkProperties["isActive"] = self.dialog.enabledCheckBox.isChecked()

        return self.linkProperties
