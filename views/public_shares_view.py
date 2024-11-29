# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

from PySide.QtGui import QCursor
from PySide.QtWidgets import QApplication
from PySide.QtCore import Qt


from delegates.public_share_delegate import PublicShareLinkDelegate
from models.share_link import PublicShareLinkListModel
from qflowview.qflowview import QFlowView
from APIClient import fancy_handle, APICallResult


class PublicSharesView(QFlowView):
    def __init__(self, parent=None):
        super(PublicSharesView, self).__init__(parent)
        self.parent = parent
        self.publicShareLinkListModel = PublicShareLinkListModel()
        self.setItemDelegate(PublicShareLinkDelegate)
        self.setModel(self.publicShareLinkListModel)
        self.get_public_sharelinks()

    def get_public_sharelinks(self):
        sharelinks = []

        def get_public_sharelink_items():
            nonlocal sharelinks
            sharelinks = self.parent.api.get_public_shared_models()
            for sl in sharelinks:
                sl.curation.parent = (
                    self.parent
                )  # this gives live api access to the item delegate's curation

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        api_result = fancy_handle(get_public_sharelink_items)
        if api_result == APICallResult.OK:
            self.publicShareLinkListModel.sharelink_list = sharelinks
            self.parent.form.publicSharesStatusLabel.setText("Most recent shown first")
            self.publicShareLinkListModel.layoutChanged.emit()

        elif api_result == APICallResult.DISCONNECTED:
            self.parent.form.publicSharesStatusLabel.setText("off-line")
            self.publicShareLinkListModel.sharelink_list = []
            self.publicShareLinkListModel.layoutChanged.emit()

        else:
            # because public shares are public, .NOT_LOGGED_IN will never happen
            self.parent.form.publicSharesStatusLabel.setText("unexpected error")
            self.publicShareLinkListModel.sharelink_list = []
            self.publicShareLinkListModel.layoutChanged.emit()
        QApplication.restoreOverrideCursor()
