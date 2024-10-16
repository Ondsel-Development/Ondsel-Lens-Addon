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
from models.share_link import PublicShareLinkListModel

logger = Utils.getLogger(__name__)


class PublicShareLinkDelegate(CurationDisplayDelegate):
    """delegate for public ShareLinks"""

    def __init__(self, index=None):
        super().__init__()
        self.share_link = index.data(PublicShareLinkListModel.ShareLinkRole)
        curation = self.share_link.curation
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

        self.setLayout(layout)
