from PySide.QtCore import Qt
from PySide.QtWidgets import QTableWidget, QAbstractItemView


class QTableWidgetWithKbReturnSupport(QTableWidget):
    """
    Just like a regular table except all the "edit" functions are blocked and Return/Enter emits the double-clicked signal.
    Useful when you want a table to act like a "selection grid"
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            row = self.currentRow()
            column = self.currentColumn()
            cell = self.item(row, column)
            self.itemDoubleClicked.emit(cell)
        else:
            super().keyPressEvent(event)
