# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import PySide.QtCore as QtCore
import FreeCADGui as Gui

from lens_command import LensCommand, LensWorkbenchManipulator, start_mdi_tab
import register_lens_handler

import WorkspaceView


Gui.addCommand("OndselLens_OndselLens", LensCommand())
Gui.addWorkbenchManipulator(LensWorkbenchManipulator())

start_mdi_tab()

QtCore.QTimer.singleShot(3000, WorkspaceView.runsAfterLaunch)
register_lens_handler.register_lens_handler()
