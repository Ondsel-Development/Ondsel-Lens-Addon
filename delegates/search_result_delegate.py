# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from PySide import QtGui
from PySide.QtGui import (
    QCursor,
)
from PySide.QtCore import Qt
import FreeCADGui as Gui

import Utils
from delegates.curation_display_delegate import CurationDisplayDelegate
from models.curation import CurationListModel

logger = Utils.getLogger(__name__)


class SearchResultDelegate(CurationDisplayDelegate):
    """delegate for search results"""

    def __init__(self, index=None):
        super().__init__()
        curation = index.data(CurationListModel.CurationRole)
        self.curation = curation
        ui_path = Utils.mod_path + "/delegates/CurationItem.ui"
        self.widget = Gui.PySideUic.loadUi(ui_path)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.widget)
        #
        # decorate the new item with data
        #
        self.widget.collectionLabel.setText(curation.nav.user_friendly_target_name())
        self.widget.titleLabel.setText(Utils.wrapify(curation.name))
        self.mousePressEvent = lambda event: self._take_action()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_image_load()
        #
        self.setLayout(layout)
