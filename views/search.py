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


class SearchResultItem(QFrame):
    def __init__(self, curation):
        super().__init__()
        self.curation_detail = curation
        ui_path = Utils.mod_path + "/views/SearchResultItem.ui"
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
        downloadIcon = QtGui.QIcon(Utils.icon_path + "cloud_download.svg")
        self.widget.downloadToolButton.setIcon(downloadIcon)
        if curation.is_downloadable():
            self.widget.downloadToolButton.setEnabled(True)
        self.image_url = curation.get_thumbnail_url()
        if ":" in self.image_url:
            mainImage = _get_pixmap_from_url(self.image_url)
            if mainImage is not None:
                self.widget.iconLabel.setPixmap(mainImage)
        elif self.image_url is not None:
            mainImage = QtGui.QIcon(Utils.icon_path + self.image_url).pixmap(
                QSize(48, 48)
            )
            self.widget.iconLabel.setPixmap(mainImage)
        #
        self.setLayout(layout)


class SearchView(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_search_results(self, resulting_curations):
        # print(resulting_curations)

        self.scrollContent = QWidget()
        scrollLayout = QVBoxLayout(self.scrollContent)
        for curation in resulting_curations:
            # item = QLabel("bling")
            item = SearchResultItem(curation)
            scrollLayout.addWidget(item)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.scrollContent.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setWidget(self.scrollContent)

    def sizeHint(self):
        return QtCore.QSize(400, 400)


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

        pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio)
        return pixmap
    except requests.exceptions.RequestException:
        pass  # no thumbnail online.
    return None
