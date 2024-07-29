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
)
from PySide.QtCore import QByteArray
from PySide.QtWidgets import QTreeView


class NewSearchResultItem(QStandardItem):
    def __init__(self, curation):
        super().__init__()
        self.curation_detail = curation
        self.setEditable(False)
        self.setText(curation.name)


class SearchView(QTreeView):
    def drawBranches(self, painter, rect, index):
        pass

    def load_search_results(self, resulting_curations):
        print(resulting_curations)
        tree_model = QStandardItemModel()
        root = tree_model.invisibleRootItem();
        for curation in resulting_curations:
            new_item = NewSearchResultItem(curation)
            root.appendRow(new_item)
        self.setModel(tree_model)



class SearchResultItem(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.item = Gui.PySideUic.loadUi(Utils.mod_path + "views/SearchResultItem.ui")
        # layout = QtGui.QVBoxLayout()
        # layout.addWidget(self.dialog)
        # self.setLayout(layout)
