# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import WorkspaceView
import PySide.QtCore as QtCore
import FreeCAD as App
import FreeCADGui as Gui

print("Loading WorkspaceView module...")
Gui.getMainWindow().addDockWidget(
    QtCore.Qt.RightDockWidgetArea,
    WorkspaceView.WorkspaceView(),
    QtCore.Qt.Orientation.Vertical,
)
