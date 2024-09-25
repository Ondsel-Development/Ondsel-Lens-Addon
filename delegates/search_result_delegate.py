from PySide import QtGui
from PySide.QtGui import (
    QCursor,
)
from PySide.QtCore import Qt, QSize
import FreeCADGui as Gui

import Utils
from delegates.curation_display_delegate import CurationDisplayDelegate, get_pixmap_from_url
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
        self.widget.titleLabel.setText(curation.name)
        self.mousePressEvent = lambda event: self._take_action()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.image_url = curation.get_thumbnail_url()
        if self.image_url is None:
            print("checkout ", curation.nav)
        elif ":" in self.image_url:
            self.widget.iconLabel.setStyleSheet("background-color:rgb(219,219,211)")
            main_image = get_pixmap_from_url(self.image_url)
            if main_image is not None:
                self.widget.iconLabel.setPixmap(main_image)
        elif self.image_url is not None:
            main_image = QtGui.QIcon(Utils.icon_path + self.image_url).pixmap(
                QSize(96, 96)
            )
            self.widget.iconLabel.setPixmap(main_image)
        #
        self.setLayout(layout)
