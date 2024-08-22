from PySide.QtCore import Qt
from PySide.QtGui import (
    QApplication,
    QCursor,
)
from qflowview.qflowview import QFlowView
from APIClient import fancy_handle, API_Call_Result

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
        self.parent.form.searchResultMessageLabel.setText("no results yet")

    def perform_search(self):
        resulting_curations = []

        def do_search():
            nonlocal resulting_curations
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

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        api_result = fancy_handle(do_search)
        match api_result:
            case API_Call_Result.OK:
                self.curationListModel.curation_list = resulting_curations
                if len(resulting_curations) == 0:
                    self.parent.form.searchResultMessageLabel.setText("no results")
                else:
                    self.parent.form.searchResultMessageLabel.setText("")
                self.curationListModel.layoutChanged.emit()
            case API_Call_Result.DISCONNECTED:
                self.parent.form.searchResultMessageLabel.setText("offline")
                self.curationListModel.curation_list = []
                self.curationListModel.layoutChanged.emit()
            case _:
                # because search is public, .NOT_LOGGED_IN will never happen
                self.parent.form.searchResultMessageLabel.setText("unexpected error")
                self.curationListModel.curation_list = []
                self.curationListModel.layoutChanged.emit()
        QApplication.restoreOverrideCursor()
