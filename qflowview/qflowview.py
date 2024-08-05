# sourced from QT docs and other places including
# https://github.com/baoboa/pyqt5/blob/master/examples/layouts/flowlayout.py

from PySide.QtCore import Qt, QSize, QRect, QPoint, QAbstractListModel
from PySide.QtGui import QScrollArea, QSizePolicy

class QFlowView(QScrollArea):
    def __init__(self, parent=None, margin=0, spacing=1):
        super(QFlowView, self).__init__(parent)
        self.fv_delegate = None
        self.fv_model = None

    def setItemDelegate(self, delegate):
        self.fv_delegate = delegate
        print(delegate)

    def setModel(self, model: QAbstractListModel):
        self.fv_model = model
        self.fv_model.layoutChanged.connect(self.onLayoutChange)
        print(model)

    def onLayoutChange(self):
        print("layout change!")
