# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2024 Ondsel <development@ondsel.com>                    *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import os
import datetime

import requests
import tempfile

import Utils

from PySide import QtCore, QtGui
from PySide.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QLabel,
    QDialog,
    QFileDialog,
    QDialogButtonBox,
    QPushButton,
    QGridLayout,
    QApplication,
)

import FreeCAD as App
import FreeCADGui as Gui
import Part

logger = Utils.getLogger(__name__)


NAME_COMMAND = "OndselLens_AddReloadableObject"
PROP_FILEPATH = "FilePath"
PROP_URL = "Url"
PROP_IMPORT_TIME = "ImportDateTime"


class ReloadableObject:

    def __init__(self, obj):
        obj.Proxy = self

        self.group = "Source"
        self.state = False

        obj.addProperty(
            "App::PropertyFile", PROP_FILEPATH, self.group, "Path to a file"
        ).FilePath = ""

        obj.addProperty(
            "App::PropertyString", PROP_URL, self.group, "URL to a file"
        ).Url = ""

        obj.addProperty(
            "App::PropertyString",
            PROP_IMPORT_TIME,
            self.group,
            "The time when object was imported",
        )

        # obj.addProperty(
        #     "App::PropertyString", PROP_ETAG, self.group, "The ETag of a URL"
        # )

        # for prop in [PROP_IMPORT_TIME, PROP_ETAG]:
        for prop in [PROP_IMPORT_TIME]:
            obj.setEditorMode(
                prop,
                App.PropertyType.Prop_Hidden | App.PropertyType.Prop_ReadOnly,
            )

    def has_step_extension(self, path_file):
        lowered = path_file.lower()
        return lowered.endswith(".stp") or lowered.endswith(".step")

    def onChanged(self, obj, prop):
        if prop == PROP_FILEPATH:
            path_file = obj.FilePath
            self.set_object_to_file(obj, path_file)
        elif prop == PROP_URL:
            url = obj.Url
            self.set_object_to_url(obj, url)

    def execute(self, obj):
        self.state = self.has_file_changed(obj)

    def has_file_changed(self, obj):
        if not self.is_valid_step_file(obj.FilePath):
            return False

        LastModified = os.path.getmtime(obj.FilePath)
        dt_object = datetime.datetime.strptime(
            obj.ImportDateTime, "%a %b %d %H:%M:%S %Y"
        )
        time_string_mtime = dt_object.timestamp()

        return LastModified > time_string_mtime

    def set_object_to_file(self, obj, path_file):
        if self.has_step_extension(path_file):
            self.load_file(obj, path_file)

            # update the label
            label = os.path.splitext(os.path.basename(path_file))[0]
            obj.Label = label
        else:
            logger.warn(f"{path_file} is not a STEP file")

    def set_object_to_url(self, obj, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type")
            if content_type != "text/plain; charset=utf-8":
                logger.warn(f"URL {url} does not point to a STEP file")
                return

            name_file = os.path.basename(url)

            with tempfile.TemporaryDirectory() as temp_dir:
                path_file = os.path.join(temp_dir, name_file)

                with open(path_file, "wb") as temp_file:
                    temp_file.write(response.content)

                self.set_object_to_file(obj, path_file)
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while downloading: {e}")

    def is_valid_step_file(self, path_file):
        return (
            path_file != ""
            and os.path.exists(path_file)
            and os.path.isfile(path_file)
            and self.has_step_extension(path_file)
        )

    def load_file(self, obj, path_file):
        if self.is_valid_step_file(path_file):
            shape = self.import_step_file(obj, path_file)
            obj.Shape = shape
            obj.ImportDateTime = QtCore.QDateTime.currentDateTime().toString()

    def import_step_file(self, obj, path_file):
        # Import the STEP file and create a shape
        shape = Part.Shape()
        shape.read(path_file)
        return shape

    def dumps(self):
        return None

    def loads(self, state):
        return None


class ReloadableObjectViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        self.Object = vobj.Object

    def doubleClicked(self, vobj):
        return self.setEditPanel(vobj)

    def setEditPanel(self, vobj):
        obj = vobj.Object
        if not Gui.Control.activeDialog():
            panel = TaskPanel(obj)
            Gui.Control.showDialog(panel)
            return True

        return False

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def onChanged(self, vp, prop):
        pass

    def getIcon(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        if self.Object.Proxy.has_file_changed(self.Object):
            icon = f"{current_directory}{os.path.sep}reloadable-update.svg"
        else:
            icon = f"{current_directory}{os.path.sep}reloadable.svg"

        return icon

    def updateData(self, obj, prop):
        pass

    def dumps(self):
        return None

    def loads(self, state):
        return None


class TaskPanel:
    def __init__(self, obj):
        self.obj = obj
        current_directory = os.path.dirname(os.path.realpath(__file__))
        self.form = Gui.PySideUic.loadUi(
            current_directory + os.path.sep + "taskpanel.ui"
        )

        self.form.lineEditFilePath.setText(obj.FilePath)
        self.form.lineEditUrl.setText(obj.Url)
        self.form.buttonBrowse.clicked.connect(self.browse_file)
        self.form.lineEditFilePath.setText(self.obj.FilePath)

        # set the refresh button state
        self.form.buttonRefresh.setEnabled(self.is_refresh_enabled())

        self.form.buttonRefresh.clicked.connect(self.refresh)
        App.ActiveDocument.openTransaction("update Reloadable Object")

    def is_refresh_enabled(self):
        return bool(
            (self.obj.FilePath and self.obj.Proxy.has_file_changed(self.obj))
            or self.obj.Url
        )

    def get_values(self):
        file_path = self.form.lineEditFilePath.text()
        url = self.form.lineEditUrl.text()
        return file_path, url

    def refresh(self):
        file_path, url = self.get_values()
        if file_path:
            self.obj.Proxy.set_object_to_file(self.obj, file_path)
        elif url:
            self.obj.Proxy.set_object_to_url(self.obj, url)

    def browse_file(self):
        dialog = create_file_dialog(self.form)

        if dialog.exec():
            file_path = dialog.selectedFiles()[0]
            if file_path:
                self.form.lineEditFilePath.setText(file_path)
                self.obj.FilePath = file_path

    def accept(self):
        file_path, url = self.get_values()
        self.obj.FilePath = file_path
        self.obj.Url = url
        App.ActiveDocument.commitTransaction()
        Gui.Control.closeDialog()

    def reject(self):
        App.ActiveDocument.abortTransaction()
        Gui.Control.closeDialog()


class FileOrURLDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(FileOrURLDialog, self).__init__(parent)
        self.setWindowTitle("Select a File or Enter a URL:")

        self.info_label = QLabel("Select either a file or a URL")

        self.file_label = QLabel("File Path:", self)
        self.file_input = QLineEdit(self)
        self.browse_button = QPushButton("...", self)
        self.browse_button.clicked.connect(self.browse_file)

        self.url_label = QLabel("URL:", self)
        self.url_input = QLineEdit(self)

        # Check clipboard for URL
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            self.url_input.setText(clipboard.text())

        layout = QGridLayout()

        # Add widgets to layout
        layout.addWidget(self.file_label, 0, 0)
        layout.addWidget(self.file_input, 0, 1)
        layout.addWidget(self.browse_button, 0, 2)

        layout.addWidget(self.url_label, 1, 0)
        layout.addWidget(self.url_input, 1, 1, 1, 2)  # Span across two columns

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.info_label)
        main_layout.addLayout(layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def browse_file(self):
        dialog = create_file_dialog(self)

        if dialog.exec():
            file_path = dialog.selectedFiles()[0]
            self.file_input.setText(file_path)

    def get_inputs(self):
        return self.file_input.text(), self.url_input.text()


def create_file_dialog(parent):
    dialog = QFileDialog(parent, "Select a STEP file")
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setNameFilters(["STEP files (*.step *.stp)"])

    return dialog


class ReloadableObjectCommand:
    def GetResources(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        return {
            "MenuText": "Add Reloadable Object",
            "ToolTip": "Create a ReloadableObject and import a STEP file",
            "Pixmap": f"{current_directory}{os.path.sep}reloadable.svg",
        }

    def Activated(self):
        doc = App.ActiveDocument
        doc.openTransaction("Add Reloadable Object")

        dialog = FileOrURLDialog()
        if dialog.exec() == QDialog.Accepted:
            file_path, url = dialog.get_inputs()
        else:
            doc.abortTransaction()
            return

        if file_path:
            step = file_path
        elif url:
            step = url
        else:
            doc.abortTransaction()
            return

        label = os.path.splitext(os.path.basename(step))[0]

        doc = App.ActiveDocument
        obj = doc.addObject("Part::FeaturePython", f"{label}")

        ReloadableObject(obj)
        ReloadableObjectViewProvider(obj.ViewObject)
        if file_path:
            obj.FilePath = file_path
        else:
            obj.Url = url

        doc.recompute()
        App.ActiveDocument.commitTransaction()

    def IsActive(self):
        return App.ActiveDocument is not None


class ReloadableObjectManipulator:
    def modifyMenuBar(self):
        return [
            {
                "insert": NAME_COMMAND,
                "menuItem": "Std_Import",
                "before": "Std_Import",
            },
        ]

    def modifyToolBars(self):
        return []

    def modifyContextMenu(self, recipient):
        if recipient == "View":
            return []


def initialize():
    if App.GuiUp:
        Gui.addCommand(NAME_COMMAND, ReloadableObjectCommand())
        manip = ReloadableObjectManipulator()
        Gui.addWorkbenchManipulator(manip)
