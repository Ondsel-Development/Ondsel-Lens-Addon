import os
from datetime import datetime
import re
import json
import shutil
import requests
import uuid
import base64
import webbrowser
import logging

import Utils
from PySide import QtCore, QtGui, QtWidgets
from PySide.QtGui import (
    QStyledItemDelegate,
    QStyle,
    QMessageBox,
    QApplication,
    QIcon,
    QAction,
    QActionGroup,
    QMenu,
    QSizePolicy,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QListView,
    QListWidgetItem,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)
from PySide.QtCore import QByteArray, Qt, QSize
from PySide.QtWidgets import QTreeView
from PySide2.QtUiTools import loadUiType
import FreeCADGui as Gui

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
        webIcon = QtGui.QIcon(Utils.icon_path + "link.svg")
        self.widget.webToolButton.setIcon(webIcon)
        self.widget.webToolButton.clicked.connect(self._goto_url)
        # downloadIcon = QtGui.QIcon(Utils.icon_path + "cloud_download.svg")
        # self.widget.downloadToolButton.setIcon(downloadIcon)
        # if curation.is_downloadable():
        #     self.widget.downloadToolButton.setEnabled(True)
        self.image_url = curation.get_thumbnail_url()
        if self.image_url is None:
            print("checkout ", curation.nav)
        elif ":" in self.image_url:
            self.widget.iconLabel.setStyleSheet("background-color:rgb(219,219,211)")
            mainImage = _get_pixmap_from_url(self.image_url)
            if mainImage is not None:
                self.widget.iconLabel.setPixmap(mainImage)
        elif self.image_url is not None:
            mainImage = QtGui.QIcon(Utils.icon_path + self.image_url).pixmap(
                QSize(96, 96)
            )
            self.widget.iconLabel.setPixmap(mainImage)
        #
        self.setLayout(layout)

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
