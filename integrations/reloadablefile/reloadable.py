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

from PySide import QtCore, QtGui
from PySide.QtWidgets import QFileDialog
from urllib.parse import urlparse
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Utils
import datetime
import os
import requests
import tempfile
import re

logger = Utils.getLogger(__name__)


NAME_COMMAND = "OndselLens_AddReloadableObject"
PROP_FILEPATH = "FilePath"
PROP_URL = "FileUrl"
PROP_IMPORT_TIME = "ImportDateTime"
PROP_SOURCE_TYPE = "SourceType"

SOURCE_TYPE_FILEPATH = "FilePath"
SOURCE_TYPE_URL = "URL"


class ReloadableObject:
    def __init__(self, obj):

        self.group = "Source"
        self.should_reload = False

        obj.addProperty(
            "App::PropertyEnumeration",
            PROP_SOURCE_TYPE,
            self.group,
            "The source type of the imported object",
        )

        obj.addProperty(
            "App::PropertyFile", PROP_FILEPATH, self.group, "Path to a file"
        ).FilePath = ""

        obj.addProperty(
            "App::PropertyString", PROP_URL, self.group, "URL to a file"
        ).FileUrl = ""

        obj.addProperty(
            "App::PropertyString",
            PROP_IMPORT_TIME,
            self.group,
            "The time when object was imported",
        )

        obj.SourceType = [SOURCE_TYPE_FILEPATH, SOURCE_TYPE_URL]

        obj.setEditorMode(PROP_URL, App.PropertyType.Prop_Hidden)
        obj.setEditorMode(PROP_IMPORT_TIME, App.PropertyType.Prop_Hidden)

        obj.Proxy = self

    def is_valid_url(self, url):
        parsed_url = urlparse(url)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)

    def is_valid_step_file(self, path_file):
        return (
            path_file != ""
            and os.path.exists(path_file)
            and os.path.isfile(path_file)
            and self.has_step_extension(path_file)
        )

    def has_step_extension(self, path_file):
        lowered = path_file.lower()
        return lowered.endswith(".stp") or lowered.endswith(".step")

    def onChanged(self, obj, prop):

        # take no action unless it's a property we care about
        if App.isRestoring() or prop not in [PROP_FILEPATH, PROP_URL, PROP_SOURCE_TYPE]:
            return

        # User has either changed the source or the source type
        if prop == PROP_FILEPATH and self.is_valid_step_file(obj.FilePath):
            self.should_reload = True
        elif prop == PROP_URL and self.is_valid_url(obj.FileUrl):
            self.should_reload = True
        elif prop == PROP_SOURCE_TYPE:
            if obj.SourceType == SOURCE_TYPE_URL:
                obj.setEditorMode(PROP_URL, App.PropertyType.Prop_None)
                obj.setEditorMode(PROP_FILEPATH, App.PropertyType.Prop_Hidden)
            else:
                obj.setEditorMode(PROP_FILEPATH, App.PropertyType.Prop_None)
                obj.setEditorMode(PROP_URL, App.PropertyType.Prop_Hidden)
            self.should_reload = True

        # Something has changed and we should reload the source
        if self.should_reload:
            self.load_source(obj)

    def execute(self, obj):
        if obj.SourceType == SOURCE_TYPE_FILEPATH:
            if self.has_file_changed(obj):
                self.should_reload = True
                if hasattr(obj, "ViewObject"):
                    obj.ViewObject.signalChangeIcon()

    def load_source(self, obj):
        if obj.SourceType == SOURCE_TYPE_URL:
            self.set_object_to_url(obj)

        elif obj.SourceType == SOURCE_TYPE_FILEPATH:  # and self.has_file_changed(obj):
            self.set_object_to_file(obj, obj.FilePath)

        self.should_reload = False

    def has_file_changed(self, obj):
        if not self.is_valid_step_file(obj.FilePath):
            return False

        if obj.ImportDateTime == "":
            return True

        LastModified = os.path.getmtime(obj.FilePath)
        dt_object = datetime.datetime.fromisoformat(obj.ImportDateTime)
        time_string_mtime = dt_object.timestamp()

        return LastModified > time_string_mtime

    def set_object_to_file(self, obj, path_file):
        if self.is_valid_step_file(path_file):
            self.load_file(obj, path_file)

            # update the label
            label = os.path.splitext(os.path.basename(path_file))[0]
            obj.Label = label
        else:
            pass

    def determine_name_file(self, url, content_disposition):
        """Determine the name for the file.

        The url is used as backup, but if there is a filename in the content
        disposition header, we use that.
        """
        name_file = os.path.basename(url)

        if content_disposition:
            matches_filename = re.findall(r'filename="(.+)"', content_disposition)
            if matches_filename:
                name_file = matches_filename[0]

        return name_file

    def set_object_to_url(self, obj):
        url = obj.FileUrl

        if not self.is_valid_url(url):
            return

        try:
            response = requests.get(url)
            response.raise_for_status()
            # There are different viewpoints on what the content type should
            # be.  Currently we allow all content types and the code below is
            # commented out.

            # content_type = response.headers.get("Content-Type")
            # if content_type != "text/plain; charset=utf-8":
            #     logger.warn(f"URL {url} does not point to a STEP file")
            #     return
            name_file = self.determine_name_file(
                url, response.headers.get("Content-Disposition")
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                path_file = os.path.join(temp_dir, name_file)

                with open(path_file, "wb") as temp_file:
                    temp_file.write(response.content)

                self.set_object_to_file(obj, path_file)

        except requests.exceptions.ConnectionError:
            pass

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while downloading: {e}")

    def load_file(self, obj, path_file):
        shape = self.import_step_file(obj, path_file)
        obj.Shape = shape
        obj.ImportDateTime = QtCore.QDateTime.currentDateTime().toString(
            QtCore.Qt.ISODate
        )

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
        App.ActiveDocument.openTransaction("update Reloadable Object")
        return self.setEdit(vobj)

    def setEdit(self, vobj=None, mode=0):
        if mode == 0:
            obj = vobj.Object
            if not Gui.Control.activeDialog():
                panel = TaskPanel(obj)
                Gui.Control.showDialog(panel)
                # We handled the setEdit
                return True

        # We did not handle the setEdit, let calling code do that.
        return None

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def onChanged(self, vp, prop):
        pass

    def getIcon(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        if self.Object.Proxy.has_file_changed(self.Object):
            icon = (
                f"{current_directory}{os.path.sep}/resources/"
                "reloadable-update-blue-arrow.svg"
            )
        else:
            icon = f"{current_directory}{os.path.sep}/resources/reloadable.svg"

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

        self.form.radioButtonURL.setChecked(True)
        self.form.buttonBrowse.clicked.connect(self.browse_file)

        self.form.radioButtonURL.toggled.connect(lambda: self.dirty())
        self.form.radioButtonFile.toggled.connect(lambda: self.dirty())
        self.form.lineEditFilePath.textChanged.connect(lambda: self.dirty())
        self.form.lineEditUrl.textChanged.connect(lambda: self.dirty())

        self.get_values(obj)

    def get_values(self, obj):

        self.form.lineEditFilePath.setText(obj.FilePath)
        self.form.lineEditUrl.setText(obj.FileUrl)

        if obj.SourceType == SOURCE_TYPE_URL:
            self.form.radioButtonURL.setChecked(True)

        elif obj.SourceType == SOURCE_TYPE_FILEPATH:
            self.form.radioButtonFile.setChecked(True)

        # check if we're dirty
        if obj.SourceType == SOURCE_TYPE_URL and obj.FileUrl != "":
            self.is_dirty = True
        elif obj.SourceType == SOURCE_TYPE_FILEPATH:
            self.is_dirty = obj.Proxy.has_file_changed(obj)

    def dirty(self):
        self.is_dirty = True

    def set_values(self):
        if not self.is_dirty:
            return

        if self.form.radioButtonURL.isChecked():
            self.obj.SourceType = SOURCE_TYPE_URL
        else:
            self.obj.SourceType = SOURCE_TYPE_FILEPATH

        self.obj.FileUrl = self.form.lineEditUrl.text()
        self.obj.FilePath = self.form.lineEditFilePath.text()
        self.is_dirty = False

    def browse_file(self):
        dialog = create_file_dialog(self.form)

        if dialog.exec():
            file_path = dialog.selectedFiles()[0]
            if file_path:
                self.form.lineEditFilePath.setText(file_path)

    def accept(self):
        self.set_values()
        App.ActiveDocument.commitTransaction()
        Gui.Control.closeDialog()

    def reject(self):
        App.ActiveDocument.abortTransaction()
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        """getStandardButtons() ... returns the Buttons for the task panel."""
        return (
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Apply
            | QtGui.QDialogButtonBox.Cancel
        )

    def clicked(self, button):
        """
        clicked(button) ... callback invoked when the user presses any of the task
        panel buttons.
        """
        if button == QtGui.QDialogButtonBox.Apply:
            self.set_values()


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
            "Pixmap": f"{current_directory}{os.path.sep}/resources/reloadable.svg",
        }

    def Activated(self):
        doc = App.ActiveDocument
        doc.openTransaction("Add Reloadable Object")

        label = "Reloadable"
        obj = doc.addObject("Part::FeaturePython", f"{label}")

        ReloadableObject(obj)
        obj.ViewObject.Proxy = ReloadableObjectViewProvider(obj.ViewObject)
        obj.ViewObject.Proxy.setEdit(obj.ViewObject, 0)

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
