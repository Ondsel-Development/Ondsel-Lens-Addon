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
from PySide.QtCore import QByteArray, Qt
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
        self.widget.collectionLabel.setText(curation.nav.user_friendly_target_name())
        self.widget.titleLabel.setText(curation.name)
        webIcon = QtGui.QIcon(Utils.icon_path + "link.svg")
        self.widget.webToolButton.setIcon(webIcon)
        downloadIcon = QtGui.QIcon(Utils.icon_path + "cloud_download.svg")
        self.widget.downloadToolButton.setIcon(downloadIcon)
        if curation.is_downloadable():
            self.widget.downloadToolButton.setEnabled(True)

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
