from PySide.QtCore import Qt
from PySide.QtGui import (
    QApplication,
    QCursor,
)

from qflowview.qflowview import QFlowView

from models.curation import CurationListModel
from delegates.search import SearchResultDelegate


class SearchResultsView(QFlowView):
    def __init__(self, parent=None):
        super(SearchResultsView, self).__init__(parent)
        self.parent = parent
        self.curationListModel = CurationListModel()
        self.setItemDelegate(SearchResultDelegate)
        self.setModel(self.curationListModel)
        self.parent.form.searchBtn.clicked.connect(self.perform_search)
        self.parent.form.searchLineEdit.returnPressed.connect(self.perform_search)

    def perform_search(self):
        QApplication.setOverrideCursor(
            QCursor(Qt.WaitCursor)
        )  # sets the hourglass, etc.
        searchTargetIndex = self.parent.form.searchTargetComboBox.currentIndex()
        searchTarget = [
            None,  # All
            "shared-models",  # Share Links
            "workspaces",  # Workspaces
            "users",  # Users
            "organizations",  # Organizations
        ][searchTargetIndex]
        searchText = self.parent.form.searchLineEdit.text()
        resulting_curations = self.parent.api.get_search_results(
            searchText, searchTarget
        )
        self.curationListModel.curation_list = resulting_curations
        self.curationListModel.layoutChanged.emit()
        QApplication.restoreOverrideCursor()
