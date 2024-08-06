# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

from PySide.QtCore import Qt, QAbstractListModel, QModelIndex


class ShareLinkModel(QAbstractListModel):
    """
    Manages a list of ShareLinks.  Links have the following attributes
    link = {
        "cloneModelId": "string",
        "title": "string",
        "description": "string",
        "protection": string(enum),
        "pin": optional(string),
        "versionFollowing": string(enum),
        "canViewModel": true,
        "canViewModelAttributes": false,
        "canUpdateModel": false,
        "canExportFCStd": false,
        "canExportSTEP": false,
        "canExportSTL": false,
        "canExportOBJ": false,
        "dummyModelId": "string",
        "canDownloadDefaultModel": True,
        "isSystemGenerated": False,
        }
    """

    ShortNameRole = Qt.UserRole + 1
    UrlRole = Qt.UserRole + 2
    CreatedRole = Qt.UserRole + 3
    ActiveRole = Qt.UserRole + 4
    EditLinkRole = Qt.UserRole + 5

    def __init__(self, model_id, apiClient, parent=None):
        super().__init__(parent)
        self.links = []
        self.model_id = model_id
        self.apiClient = apiClient

        self.refresh_model()

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        rowdata = self.links[index.row()]

        if role == Qt.DisplayRole:
            return f"{rowdata['title']} ({rowdata['description']})"
        elif role == self.UrlRole:
            return rowdata["_id"]
        elif role == self.ActiveRole:
            return rowdata["active"]
        elif role == self.EditLinkRole:
            row_data = self.links[index.row()]
            return row_data

        return None

    def update_link(self, index, linkData):
        # throws an APIClientException
        if not index.isValid():
            return False

        row = index.row()
        if not (0 <= row < len(self.links)):
            return False

        link = self.links[row]
        linkData["_id"] = link["_id"]
        self.apiClient.updateSharedModel(linkData)
        self.refresh_model()

        # self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def rowCount(self, index=QModelIndex()):
        return len(self.links)

    def refresh_model(self):
        # throws an APIClientException
        self.beginResetModel()
        self.links = []

        params = {"cloneModelId": self.model_id}
        shared_models = self.apiClient.getSharedModels(params=params)

        for sm in shared_models:
            canExport = sm.get("canExportModel", True)
            link = {
                "_id": sm["_id"],
                "isActive": sm["isActive"],
                "isSystemGenerated": sm.get("isSystemGenerated", False),
                "title": sm["title"],
                "description": sm.get("description", ""),
                "protection": sm["protection"],
                "versionFollowing": sm["versionFollowing"],
                "canViewModel": sm["canViewModel"],
                "canViewModelAttributes": sm["canViewModelAttributes"],
                "canUpdateModel": sm["canUpdateModel"],
                "canExportFCStd": sm.get("canExportFCStd", canExport),
                "canExportSTEP": sm.get("canExportSTEP", canExport),
                "canExportSTL": sm.get("canExportSTL", canExport),
                "canExportOBJ": sm.get("canExportOBJ", canExport),
                "dummyModelId": sm.get("dummyModelId", None),
                "canDownloadDefaultModel": sm.get("canDownloadDefaultModel", canExport),
                "cloneModelId": sm.get("cloneModelId"),
            }
            if link["protection"] == "Pin":
                # a "find" never returns a PIN for security reasons, so
                # make a singular query to get that detail.
                fullSharedModel = self.apiClient.getSharedModel(sm["_id"])
                link["pin"] = fullSharedModel.get("pin", "")
            else:
                link["pin"] = ""

            self._add_link(link)
        self.endResetModel()

    def compute_direct_link(self, model_id):
        return f"{self.apiClient.get_base_url()}share/{model_id}"

    def compute_forum_shortcode(self, model_id):
        return f"[ondsel]{model_id}[/ondsel]"

    def compute_iframe(self, model_id):
        direct_link = self.compute_direct_link(model_id)
        return (
            '<iframe width="560" height="315" '
            f'src="{direct_link}" title="Ondsel"></iframe>'
        )

    def dump(self):
        print("dumping model")
        for link in self.links:
            print(link)

    def delete_link(self, link_id):
        # raises an APIClientException
        self.apiClient.deleteSharedModel(link_id)
        self.refresh_model()

    def add_new_link(self, link):
        """public method to add link to the model on server

        raises an APIClientException
        """

        link["cloneModelId"] = self.model_id

        if link.get("isActive", None) is not None:
            link.pop("isActive")

            self.apiClient.createSharedModel(link)
            self.refresh_model()

    def _add_link(self, link):
        """private method to add to the qabstractTableModel"""

        row = len(self.links)
        # Add the new item to the links list
        self.beginInsertRows(QModelIndex(), row, row)
        self.links.append(link)
        self.endInsertRows()

        return True
