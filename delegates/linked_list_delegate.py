from PySide.QtWidgets import QStyledItemDelegate, QStyle
from PySide import QtCore, QtGui


class LinkListDelegate(QStyledItemDelegate):
    iconShareClicked = QtCore.Signal(QtCore.QModelIndex)
    iconEditClicked = QtCore.Signal(QtCore.QModelIndex)
    iconDeleteClicked = QtCore.Signal(QtCore.QModelIndex)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        name = index.data(QtCore.Qt.DisplayRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        icon_copy_rect = QtCore.QRect(
            option.rect.right() - 60, option.rect.top(), 16, 16
        )
        icon_edit_rect = QtCore.QRect(
            option.rect.right() - 40, option.rect.top(), 16, 16
        )
        icon_delete_rect = QtCore.QRect(
            option.rect.right() - 20, option.rect.top(), 16, 16
        )
        text_rect = QtCore.QRect(
            option.rect.left() + 4,
            option.rect.top(),
            option.rect.width() - 60,
            option.rect.height(),
        )

        icon_copy = QtGui.QIcon.fromTheme("back", QtGui.QIcon(":/icons/edit-copy.svg"))
        icon_edit = QtGui.QIcon.fromTheme(
            "back", QtGui.QIcon(":/icons/Std_DlgParameter.svg")
        )
        icon_delete = QtGui.QIcon.fromTheme(
            "back", QtGui.QIcon(":/icons/edit_Cancel.svg")
        )

        icon_copy.paint(painter, icon_copy_rect)
        icon_edit.paint(painter, icon_edit_rect)
        icon_delete.paint(painter, icon_delete_rect)
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, name)

    def editorEvent(self, event, model, option, index):
        if not index.isValid():
            return False
        if (
            event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.LeftButton
        ):
            icon_share_rect = QtCore.QRect(
                option.rect.right() - 60, option.rect.top(), 16, 16
            )
            icon_edit_rect = QtCore.QRect(
                option.rect.right() - 40, option.rect.top(), 16, 16
            )
            icon_delete_rect = QtCore.QRect(
                option.rect.right() - 20, option.rect.top(), 16, 16
            )

            if icon_share_rect.contains(event.pos()):
                self.iconShareClicked.emit(index)
                return True
            elif icon_edit_rect.contains(event.pos()):
                self.iconEditClicked.emit(index)
                return True
            elif icon_delete_rect.contains(event.pos()):
                self.iconDeleteClicked.emit(index)
                return True
        # If the click wasn't on any icon, select the item as normal
        return super().editorEvent(event, model, option, index)
