from PySide import QtGui
from PySide.QtGui import (
    QCursor,
)
from PySide.QtCore import Qt, QSize
import FreeCADGui as Gui

import Utils
from Utils import EventName
from delegates.curation_display_delegate import (
    CurationDisplayDelegate,
    get_pixmap_from_url,
)
from models.curation import CurationListModel

logger = Utils.getLogger(__name__)


class SearchResultDelegate(CurationDisplayDelegate):
    """delegate for search results"""

    def __init__(self, index=None):
        super().__init__()
        self.download_sharelink_event_name = EventName.SEARCH_TAB_DOWNLOAD_SHARELINK
        self.download_workspace_file_event_name = (
            EventName.SEARCH_TAB_DOWNLOAD_WORKSPACE_FILE
        )
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
        self.start_image_load()
        #
        self.setLayout(layout)
