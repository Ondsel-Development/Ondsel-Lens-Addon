from PySide.QtWidgets import QStyle
from PySide import QtCore, QtGui
from PySide.QtWidgets import QStyledItemDelegate
from Utils import renderFileName
from models.workspace_model import WorkspaceModel


# Simple delegate drawing an icon and text
class FileListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the data for the current index
        if not index.isValid():
            return

        fileName, status, isFolder = index.data(
            WorkspaceModel.NameStatusAndIsFolderRole
        )

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        icon_rect = QtCore.QRect(option.rect.left(), option.rect.top(), 16, 16)
        text_rect = QtCore.QRect(
            option.rect.left() + 20,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height(),
        )
        if isFolder:
            icon = QtGui.QIcon.fromTheme("back", QtGui.QIcon(":/icons/folder.svg"))
        else:
            icon = QtGui.QIcon.fromTheme(
                "back", QtGui.QIcon(":/icons/document-new.svg")
            )
        icon.paint(painter, icon_rect)
        textToDisplay = renderFileName(fileName)
        if status:
            textToDisplay += " (" + str(status) + ")"

        fontMetrics = painter.fontMetrics()
        elidedText = fontMetrics.elidedText(
            textToDisplay, QtGui.Qt.ElideRight, option.rect.width()
        )
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, elidedText)
