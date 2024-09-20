import requests
import webbrowser

import Utils
from PySide import QtCore, QtGui, QtWidgets
from PySide.QtGui import (
    QPixmap,
    QFrame,
    QCursor,
)
from PySide.QtCore import QByteArray, Qt, QSize
import FreeCADGui as Gui

from components.choose_download_action_dialog import ChooseDownloadActionDialog
from models.curation import CurationListModel

logger = Utils.getLogger(__name__)


class SearchResultDelegate(QFrame):
    """delegate for search results"""

    def __init__(self, index=None):
        super().__init__()
        if index is None:
            return  # if none, this is a dummy object

        curation = index.data(CurationListModel.CurationRole)
        self.curation = curation
        ui_path = Utils.mod_path + "/delegates/SearchResultItem.ui"
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
            main_image = _get_pixmap_from_url(self.image_url)
            if main_image is not None:
                self.widget.iconLabel.setPixmap(main_image)
        elif self.image_url is not None:
            main_image = QtGui.QIcon(Utils.icon_path + self.image_url).pixmap(
                QSize(96, 96)
            )
            self.widget.iconLabel.setPixmap(main_image)
        #
        self.setLayout(layout)

    def _take_action(self):
        if self.curation.collection == "shared-models":
            data_parent = self.curation.parent
            dlg = ChooseDownloadActionDialog(self.curation.name, data_parent)
            overall_response = dlg.exec()
            if overall_response != 0:
                if dlg.answer == ChooseDownloadActionDialog.OPEN_ON_WEB:
                    self._goto_url()
                elif dlg.answer == ChooseDownloadActionDialog.DL_TO_MEM:
                    downloaded_filename = Utils.download_shared_model_to_memory(
                        self.curation.parent.api, str(self.curation._id)
                    )
                    if downloaded_filename is False:
                        logger.warn("Unable to download; opening in browser instead.")
                        self._goto_url()
                    else:
                        logger.warn(
                            f"Downloaded {downloaded_filename} into memory. Be sure to save to disk if you want to keep the model."
                        )
        else:
            self._goto_url()

    def _goto_url(self):
        base = Utils.env.lens_url
        url = self.curation.nav.generate_url(base)
        logger.info(f"open {url}")
        if not webbrowser.open(url):
            logger.warn(f"Failed to open {url} in the browser")


def _get_pixmap_from_url(thumbnailUrl):
    try:
        response = requests.get(thumbnailUrl)
        image_data = response.content
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        # Crop the image to a square
        width = pixmap.width()
        height = pixmap.height()
        size = min(width, height)
        diff = abs(width - height)
        left = diff // 2
        pixmap = pixmap.copy(left, 0, size, size)

        pixmap = pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio)
        return pixmap
    except requests.exceptions.RequestException:
        pass  # no thumbnail online.
    return None
