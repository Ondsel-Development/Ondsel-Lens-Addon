# SPDX-FileCopyrightText: 2023 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

import FreeCADGui as Gui

from lens_command import (
    LensCommand,
    LensWorkbenchManipulator,
    start_mdi_tab,
    init_toolbar_icon,
    ensure_mdi_tab,
)
import integrations.reloadablefile.reloadable as reloadable
import register_lens_handler


Gui.addCommand("OndselLens_OndselLens", LensCommand())
Gui.addWorkbenchManipulator(LensWorkbenchManipulator())


start_mdi_tab()
init_toolbar_icon()
ensure_mdi_tab()

register_lens_handler.register_lens_handler()
reloadable.initialize()
