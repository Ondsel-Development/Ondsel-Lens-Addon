import copy

import requests
import webbrowser

import Utils
import handlers
from PySide.QtGui import QPixmap, QFrame, QIcon
from PySide.QtCore import Qt, QThread, QObject, Signal, QSize

from components.choose_download_action_dialog import ChooseDownloadActionDialog
from components.choose_from_lens_dialog import ChooseFromLensDialog
from components.choose_workspace_action_dialog import ChooseWorkspaceActionDialog

logger = Utils.getLogger(__name__)


class CurationDisplayDelegate(QFrame):
    """delegate for curation display in general; should be used by children via inheritance not directly"""

    def __init__(self, index=None):
        super().__init__()
        if index is None:
            return  # if none, this is a dummy object
        self.curation = None  # to be properly set by the child class
        self.download_sharelink_event_name = (
            "invalid-download-sharelink-file"  # should be reset by child class
        )
        self.download_workspace_file_event_name = "invalid-download-workspace-file"

    def start_image_load(self):
        self._preload_icon()
        image_url = (
            self.curation.get_thumbnail_url()
        )  # sadly, this cannot be queued because API does not work in thread for some reason
        self.thread = QThread()
        self.worker = _GetCurationImage()
        self.worker.image_url = image_url
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self._image_available)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _preload_icon(self):
        image_filename = self.curation.get_just_icon_filename()
        pixmap = QIcon(Utils.icon_path + image_filename).pixmap(QSize(96, 96))
        self.widget.iconLabel.setPixmap(pixmap)

    def _image_available(self, pixmap, image_downloaded):
        if image_downloaded:
            self.widget.iconLabel.setPixmap(pixmap)
            self.widget.iconLabel.setStyleSheet("background-color:rgb(219,219,211)")

    def _take_action(self):
        if self.curation.collection == "shared-models":
            data_parent = self.curation.parent
            dlg = ChooseDownloadActionDialog(self.curation.name, data_parent)
            overall_response = dlg.exec()
            if overall_response != 0:
                if dlg.answer == ChooseDownloadActionDialog.OPEN_ON_WEB:
                    self._goto_url()
                elif dlg.answer == ChooseDownloadActionDialog.DL_TO_MEM:
                    msg = handlers.download_shared_model_to_memory(
                        self.curation.parent.api,
                        str(self.curation._id),
                        self.download_sharelink_event_name,
                    )
                    if msg is False:
                        logger.warn("Unable to download; opening in browser instead.")
                        self._goto_url()
                    else:
                        logger.warn(
                            f"{msg}. Be sure to save to disk if you want to keep the model."
                        )
        elif self.curation.collection == "workspaces":
            data_parent = self.curation.parent
            dlg = ChooseWorkspaceActionDialog(self.curation.name, data_parent)
            overall_response = dlg.exec()
            if overall_response != 0:
                if dlg.answer == ChooseWorkspaceActionDialog.OPEN_ON_WEB:
                    self._goto_url()
                elif dlg.answer == ChooseDownloadActionDialog.DL_TO_MEM:
                    self._choose_one_file()
        else:
            self._goto_url()

    def _goto_url(self):
        base = Utils.env.lens_url
        url = self.curation.nav.generate_url(base)
        logger.info(f"open {url}")
        if not webbrowser.open(url):
            logger.warn(f"Failed to open {url} in the browser")

    def _choose_one_file(self):
        data_parent = self.curation.parent
        workspace_list = [self.curation.generateWorkspaceSummary(True)]
        dlg = ChooseFromLensDialog(workspace_list, data_parent)
        overall_response = dlg.exec()
        if overall_response == 0:
            return
        file_detail = dlg.answer["file"]
        msg = handlers.download_file_version_to_memory(
            self.curation.parent.api,
            file_detail._id,
            file_detail.currentVersion._id,
            True,
            self.download_workspace_file_event_name,
        )
        if msg is False:
            logger.warn("Unable to download; opening in browser instead.")
            self._goto_url()
        else:
            logger.warn(
                f"{msg}.  Be sure to save to disk if you want to keep the model."
            )


def get_pixmap_from_url(thumbnailUrl):
    try:
        response = requests.get(thumbnailUrl)
        image_data = response.content
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        # Crop the image to a square
        width = pixmap.width()
        height = pixmap.height()
        size = min(width, height)
        diff = abs(width - height)
        left = diff // 2
        pixmap = pixmap.copy(left, 0, size, size)

        pixmap = pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio)
        return pixmap
    except requests.exceptions.RequestException:
        pass  # no thumbnail online.
    return None


class _GetCurationImage(QObject):
    """
    This thread worker class is strictly for use by the single thread started in CurationDisplayDelegate (and it's children).
    The child will call the `start_image_load()` method of CurationDisplayDelegate during initialization. That will,
    in turn, start this thread. This thread then emits the result when image is in memory.
    """

    finished = Signal(
        QPixmap, bool
    )  # the bool is needed because "None" is still re-interpreted by the C lib as QPixMap

    def __init__(self):
        super().__init__()
        self.image_url = None

    def run(self):
        pixmap = None
        image_downloaded = False
        if self.image_url is not None and ":" in self.image_url:
            pixmap = get_pixmap_from_url(self.image_url)
            if pixmap is not None:
                image_downloaded = True
        self.finished.emit(pixmap, image_downloaded)
