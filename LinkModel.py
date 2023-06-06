from PySide.QtCore import Qt, QAbstractTableModel, QModelIndex, QDateTime


class ShareLinkModel(QAbstractTableModel):
    """
    Manages a list of ShareLinks.  Links have the following attributes
    link = {
        "cloneModelId": "string",
        "description": "string",
        "canViewModel": true,
        "canViewModelAttributes": false,
        "canUpdateModel": false,
        "canExportFCStd": false,
        "canExportSTEP": false,
        "canExportSTL": false,
        "canExportOBJ": false,
        "dummyModelId": "string"
        "canDownloadDefaultModel": True
        }
    """

    ShortNameRole = Qt.UserRole + 1
    UrlRole = Qt.UserRole + 2
    CreatedRole = Qt.UserRole + 3
    ActiveRole = Qt.UserRole + 4
    EditLinkRole = Qt.UserRole + 5

    def __init__(self, model_id, api_client, parent=None):
        super().__init__(parent)
        self.headers = ["Description", "url", "active"]
        self.links = []
        self.model_id = model_id
        self.api_client = api_client

        self.refresh_model()

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        rowdata = self.links[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return rowdata["description"]
            elif index.column() == 1:
                return rowdata["cloneModelId"]
        elif role == self.UrlRole:
                return rowdata["_id"]
        elif role == self.ActiveRole:
                return rowdata["active"]
        elif role == self.EditLinkRole:
            row_data = self.links[index.row()]
            return row_data

            # elif index.column() == 2:
            #     created = rowdata["created"]
            #     return QDateTime.fromString(created)

        elif role == Qt.CheckStateRole and index.column() == 3:
            active = rowdata["active"]
            return Qt.Checked if active else Qt.Unchecked

        return None


    def update_link(self, index, linkData):
        if not index.isValid():
            return False

        row = index.row()
        if not (0 <= row < len(self.links)):
            return False

        link = self.links[row]
        link.update(linkData)  # Update all fields in link dictionary
        self.api_client.updateSharedModel(link)

        self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def rowCount(self, index=QModelIndex()):
        return len(self.links)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def refresh_model(self):
        print("refreshing model")

        self.beginResetModel()
        self.links = []

        params = {"cloneModelId": self.model_id}
        shared_models = self.api_client.getSharedModels(params=params)

        for model in shared_models:
            canExport = model.get("canExportModel", True)
            link = {

                "_id": model["_id"],
                "description": model.get("description", ""),
                # "url": self.compute_url(model["cloneModelId"]),
                "canViewModel": model["canViewModel"],
                "canViewModelAttributes": model["canViewModelAttributes"],
                "canUpdateModel": model["canUpdateModel"],
                "canExportModelFCStd": model.get("canExportModelFCStd", canExport),
                "canExportModelSTEP": model.get("canExportModelSTEP", canExport),
                "canExportModelSTL": model.get("canExportModelSTL", canExport),
                "canExportModelOBJ": model.get("canExportModelOBJ", canExport),
                "active": model.get("isActive", True),
                "dummyModelId": model.get("dummyModelId", None),
                "canDownloadDefaultModel":  model.get("canDownloadDefaultModel", canExport),
                "cloneModelId": model.get("cloneModelId"),
            }

            self._add_link(link)
        self.endResetModel()

    def compute_url(self, model_id):
        port = ":8080"
        return f"{self.api_client.get_base_url()}{port}/share/{model_id}"

    def dump(self):
        print("dumping model")
        for link in self.links:
            print(link)

    def delete_link(self, link_id):
        print("deleting link")
        print(link_id)
        try:
            self.api_client.deleteSharedModel(link_id)
            self.refresh_model()
        except Exception as e:
            self.api_client = None
            raise e

    def add_new_link(self, link):
        """ public method to add link to the model on server """

        try:
            result = self.api_client.createSharedModel(link)
            self._add_link(result)
            self.dump()
            return result
        except Exception as e:
            raise e  # need to handle connection problem at least 


    def _add_link(self, link):
        """ private method to add to the qabstractTableModel"""
        row = len(self.links)

        # Add the new item to the links list
        self.beginInsertRows(QModelIndex(), row, row)
        self.links.append(link)
        self.endInsertRows()

        return True

