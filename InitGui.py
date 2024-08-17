# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import Utils
from lens_command import LensCommand, LensWorkbenchManipulator
import FreeCAD
import FreeCADGui as Gui
from PySide import QtGui
from PySide import QtWidgets

import WorkspaceView

def find_subwindow(main_window):
    from PySide import QtWidgets
    subwindows = main_window.findChildren(QtWidgets.QMdiSubWindow)
    for subwindow in subwindows:
        if subwindow.widget().centralWidget().objectName() == "WorkspaceView":
            return subwindow
    return None


print("STARTING UP")
Gui.addCommand("OndselLens_OndselLens", LensCommand())
Gui.addWorkbenchManipulator(LensWorkbenchManipulator())
main_window = Gui.getMainWindow()
subwindow = find_subwindow(main_window)
if subwindow:
    mdi_area = main_window.findChild(QtWidgets.QMdiArea)
    mdi_area.setActiveSubWindow(subwindow)
else:
    if WorkspaceView.wsv:
        del WorkspaceView.wsv
    WorkspaceView.wsv = WorkspaceView.WorkspaceView(main_window)
    main_window.addWindow(WorkspaceView.wsv)
    subwindow = find_subwindow(main_window)
    if subwindow:
        subwindow.setWindowTitle("Ondsel Lens")
        subwindow.setWindowIcon(QtGui.QIcon(Utils.icon_ondsel_path_connected))
        subwindow.showMaximized()

# QtCore.QTimer.singleShot(5000, WorkspaceView.runsAfterLaunch)

print("DONE STARTING")
