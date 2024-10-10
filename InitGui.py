# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import PySide.QtCore as QtCore
import FreeCADGui as Gui

import Utils
from lens_command import (
    LensLauncherCommand,
    LensWorkbenchManipulator,
    start_mdi_tab,
    init_toolbar_icon,
    ensure_mdi_tab, LensUploadAsCommand,
)
import integrations.reloadablefile.reloadable as reloadable
import register_lens_handler


Gui.addCommand(Utils.LENS_LAUNCHER_NAME_COMMAND, LensLauncherCommand())
Gui.addCommand(Utils.LENS_UPLOADAS_NAME_COMMAND, LensUploadAsCommand())
Gui.addWorkbenchManipulator(LensWorkbenchManipulator())


start_mdi_tab()
init_toolbar_icon()
ensure_mdi_tab()

register_lens_handler.register_lens_handler()
reloadable.initialize()
