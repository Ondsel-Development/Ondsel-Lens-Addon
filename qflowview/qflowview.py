# sourced from QT docs and other places including
# https://github.com/baoboa/pyqt5/blob/master/examples/layouts/flowlayout.py

from PySide.QtCore import Qt, QSize, QRect, QPoint, QAbstractListModel
from PySide.QtGui import QScrollArea, QSizePolicy

class _QFlowViewFace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.scrollLayout = OFlowLayout(parent)
        self.setLayout(self.scrollLayout)
        self.children = []

    def load_results(self, item_list):
        for item in item_list:
            new_delegate = parent.fv_delegate(item)
            self.children.append(new_delegate)
            self.scrollLayout.addWidget(self.children[-1])

    def remove_all_results(self):
        while self.scrollLayout.count():
            item = self.scrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clearLayout(item.layout())
        self.children = []


class QFlowView(QScrollArea):
    def __init__(self, parent=None, margin=0, spacing=1):
        super(QFlowView, self).__init__(parent)
        self.fv_delegate = None
        self.fv_model = None
        self.widget = None

    def _consider_setup(self):
        if self.widget is None:
            if self.fv_delegate is not None:
                if self.fv_model is not None:
                    self._live_setup()

    def _live_setup(self):
        # this should only run once
        self.widget = QWidget()
        self.vbox = QVBoxLayout()
        self.resultWidget = _QFlowViewFace(self)
        self.vbox.addWidget(
            self.resultWidget
        )  # Yes, only one item: the resulting widget, which is flowing
        self.widget.setLayout(self.vbox)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)

    def setItemDelegate(self, delegate):
        self.fv_delegate = delegate
        _consider_setup()

    def setModel(self, model: QAbstractListModel):
        self.fv_model = model
        self.fv_model.layoutChanged.connect(self.onLayoutChange)
        _consider_setup()

    def onLayoutChange(self):
        if self.widget is not None:
            print("layout change!")
            self.resultWidget

            da_list = [] # TODO using fv_model

            self.vbox.removeWidget(self.resultWidget)
            # yes, we are completedly relying on python's memory manager clean up all those SearchResultItems()
            self.resultWidget.remove_all_results()
            del self.resultWidget
            self.resultWidget = _QFlowViewFace(self) # note: just added self in param
            self.resultWidget.load_results(da_list)
            self.vbox.addWidget(self.resultWidget)
        else:
            print("QFlowView class not fully setup. Is delegate or model not set yet?")

    def sizeHint(self):
        return QtCore.QSize(1200, 400)
