from PySide.QtWidgets import QLabel
from PySide import QtGui
from PySide.QtGui import (
    QCursor,
)
from PySide.QtCore import Qt, QSize
import FreeCADGui as Gui

import Utils
from delegates.curation_display_delegate import (
    CurationDisplayDelegate,
    get_pixmap_from_url,
)
from models.promotion import PromotionListModel

logger = Utils.getLogger(__name__)


class PromotionDelegate(CurationDisplayDelegate):
    """delegate for promotion listing"""

    def __init__(self, index=None):
        super().__init__()
        promotion = index.data(PromotionListModel.PromotionRole)
        self.promotion = promotion
        curation = promotion.curation
        self.curation = curation
        notation = promotion.notation
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
        # insert Notation detail (if there is any)
        #
        if notation.message:
            blue_msg = f"<font color='#add8e6'>{notation.message}</font>"
            blue_label = QLabel(blue_msg)
            blue_label.setWordWrap(True)
            layout.addWidget(blue_label)
        self.setLayout(layout)
