from PySide.QtGui import QStyledItemDelegate, QApplication, QStyle
from PySide.QtCore import QSize, QRect
# from PySide import QtCore, QtGui, QtWidgets

from views.search import SearchResultItemView

padding=4
margin=4
x_size = 128
y_size = 192
size = QSize(x_size, y_size)
size_as_rect = QRect(0, 0, x_size, y_size)
size_with_padding = QSize(x_size + padding, y_size + padding)
char_height=12

class CurationDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.img = None

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        # gather data
        baseX = option.rect.topLeft().x()
        baseY = option.rect.topLeft().y()
        model = index.model()
        row = index.row()
        curation = model.curation_list[row]
        sri = SearchResultItemView(curation)
        self.img = sri.grab()
        painter.drawPixmap(baseX, baseY, self.img)

    def sizeHint(self, option, index):
        if self.img is None:
            return QSize(size_with_padding)
        new_size = QSize(self.img.width()+padding, self.img.height()+padding)
        return new_size

