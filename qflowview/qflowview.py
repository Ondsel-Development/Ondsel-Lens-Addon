# sourced from QT docs and other places including
# https://github.com/baoboa/pyqt5/blob/master/examples/layouts/flowlayout.py

from PySide.QtCore import Qt, QSize, QRect, QPoint, QAbstractListModel
from PySide.QtGui import QScrollArea, QSizePolicy, QWidget, QVBoxLayout

from qflowview.flowlayout import FlowLayout

from inspect import isclass


class _QFlowViewFace(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.scrollLayout = FlowLayout(parent)
        self.setLayout(self.scrollLayout)
        self.children = []

    def load_results(self):
        item_list_model = self.parent.fv_model
        count = item_list_model.rowCount(0)  # see documentation for QFlowView
        for indexInt in range(0, count):
            index = item_list_model.createIndex(indexInt, 0)
            new_delegate = self.parent.fv_delegate_class(index)
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
    """
    QFlowView is a Model-View-Delegate-style View class. However, it expands
    to be as wide as possible and place a toolbar on the right. Items are
    added horizontally from left to right. After one row is full, the next
    item is added to the next row. The items need not be of the same size.

    It has the benefit of behaving like the QTreeView/QListView/QTableView
    built-in classes in regards to data handling. It does not, however, use
    the high-speed C-level paint caching invoked by those three classes. So
    don't expect it to be crazy fast like QTreeView.

    The model in `setModel` is expected to inherit from QAbstractListModel
    The data in this model should all be in "column 0" and provide a
    `rowCount(0)` answer. It also needs a `data` response with any or
    all roles desired.

    The delegate in `setItemDelegate` MUST be set before anything displays.
    The parameter to `setItemDelegate` can either be the class or an instance
    of the class. If an instance, only the class is stored and the instance
    discarded. The delegate class, rather than be a `QStyledItemDelegate` with
    a c-centric "paint" method, you can inherit from ANY type of viewable
    widget and support passing a `index` of type `QModelIndex` on
    initialization.

    So, for example, if:

        liveModel = MyFancyListModel()
        myArea = QFlowView()
        myArea.setItemDelegate(MyFancyDelegateWidget)
        myArea.setModel(liveModel)

    then QFlowArea will create entry:

        MyFancyDelegateWidget(index)

    The "roles" are independent of QFlowView. Only the model and delegate
    need to match up.

    Because QFlowView is a superset of QScrollArea, you can also pass
    margin=n and spacing=n parameters on creation.
    """

    def __init__(self, parent=None):
        super(QFlowView, self).__init__(parent)
        self.fv_delegate_class = None
        self.fv_model = None
        self.widget = None

    def _consider_setup(self):
        if self.widget is None:
            if self.fv_delegate_class is not None:
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

    def setItemDelegate(self, delegate_class):
        if isclass(delegate_class):
            self.fv_delegate_class = delegate_class
        else:
            self.fv_delegate_class = delegate_class.__class__
        self._consider_setup()

    def setModel(self, model: QAbstractListModel):
        self.fv_model = model
        self.fv_model.layoutChanged.connect(self.onLayoutChange)
        self._consider_setup()

    def onLayoutChange(self):
        if self.widget is not None:
            self.resultWidget
            self.vbox.removeWidget(self.resultWidget)
            # yes, we are completedly relying on python's memory manager clean up all those SearchResultItems()
            self.resultWidget.remove_all_results()
            del self.resultWidget
            self.resultWidget = _QFlowViewFace(self)  # note: just added self in param
            self.resultWidget.load_results()
            self.vbox.addWidget(self.resultWidget)
        else:
            print("QFlowView class not fully setup. Is delegate or model not set yet?")

    def sizeHint(self):
        return QSize(1200, 400)
