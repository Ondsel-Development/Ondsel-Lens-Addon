import requests
import webbrowser

import Utils
import handlers
from handlers import HandlerException
from PySide.QtGui import QPixmap, QFrame, QIcon
from PySide.QtCore import (
    Qt,
    QObject,
    Signal,
    QSize,
    QThreadPool,
    QRunnable,
    QCoreApplication,
)

from components.choose_download_action_dialog import ChooseDownloadActionDialog
from components.choose_from_lens_dialog import ChooseFromLensDialog
from components.choose_workspace_action_dialog import ChooseWorkspaceActionDialog

from Utils import wait_cursor

logger = Utils.getLogger(__name__)


class _CurationImageLoader:
    def __init__(self):
        self.thread_pool = QThreadPool()

    def load_image(self, image_url, callback):
        worker = _CurationImageWorker(image_url)
        worker.signals.finished.connect(callback)
        self.thread_pool.start(worker)

    def shutdown(self):
        self.thread_pool.waitForDone()


class _CurationImageSignals(QObject):
    finished = Signal(
        bytes, bool
    )  # the bool is needed because "None" is still re-interpreted by the C lib
    #  as QPixMap


class _CurationImageWorker(QRunnable):
    """
    This thread worker class is strictly for use by the single thread started
    in CurationDisplayDelegate (and it's children).  The child will call the
    `start_image_load()` method of CurationDisplayDelegate during
    initialization. That will, in turn, start this thread. This thread then
    emits the result when image is in memory.

    """

    def __init__(self, image_url):
        super().__init__()
        self.image_url = image_url
        self.signals = _CurationImageSignals()

    def run(self):
        image_data = None
        image_downloaded = False
        if self.image_url is not None and ":" in self.image_url:
            image_data = get_image_data_from_url(self.image_url)
            if image_data is not None:
                image_downloaded = True
        self.signals.finished.emit(image_data, image_downloaded)


class CurationDisplayDelegate(QFrame):
    """delegate for curation display in general; should be used by children via
    inheritance not directly
    """

    image_loader = _CurationImageLoader()

    def __init__(self, index=None):
        super().__init__()
        if index is None:
            return  # if none, this is a dummy object
        self.curation = None  # to be properly set by the child class

    def start_image_load(self):
        self._preload_icon()
        image_url = (
            self.curation.get_thumbnail_url()
        )  # sadly, this cannot be queued because API does not work in thread
        # for some reason
        CurationDisplayDelegate.image_loader.load_image(
            image_url, self._image_available
        )

    def _preload_icon(self):
        image_filename = self.curation.get_just_icon_filename()
        pixmap = QIcon(Utils.icon_path + image_filename).pixmap(QSize(96, 96))
        self.widget.iconLabel.setPixmap(pixmap)

    def _image_available(self, image_data, image_downloaded):
        if image_downloaded:
            pixmap = get_pixmap_from_data(image_data)
            self.widget.iconLabel.setPixmap(pixmap)
            self.widget.iconLabel.setStyleSheet("background-color:rgb(219,219,211)")

    def _try_download(self, func):
        with wait_cursor():
            try:
                name_file = func()
                handlers.warn_downloaded_file(name_file)
            except HandlerException as e:
                logger.warn(e)
                logger.warn("Unable to download; opening in browser instead.")
                self._goto_url()

    def _take_action(self):
        if self.curation.collection == "shared-models":
            with wait_cursor():
                api = self.curation.parent.api
                dlg = ChooseDownloadActionDialog(self.curation.name, api)
            overall_response = dlg.exec()
            if overall_response != 0:
                if dlg.answer == ChooseDownloadActionDialog.OPEN_ON_WEB:
                    self._goto_url()
                elif dlg.answer == ChooseDownloadActionDialog.DL_TO_MEM:
                    self._try_download(
                        lambda: handlers.download_shared_model_to_memory(
                            self.curation.parent.api, str(self.curation._id)
                        )
                    )
        elif self.curation.collection == "workspaces":
            with wait_cursor():
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
        self._try_download(
            lambda: handlers.download_file_version_to_memory(
                self.curation.parent.api,
                file_detail._id,
                file_detail.currentVersion._id,
                True,
            )
        )


def get_pixmap_from_data(image_data):
    # QPixmap should only be called on the main thread,
    # so split getting the data and creating the pixmap.
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


def get_image_data_from_url(thumbnailUrl):
    try:
        response = requests.get(thumbnailUrl)
        return response.content
    except requests.exceptions.RequestException:
        pass  # no thumbnail online.
    return None


QCoreApplication.instance().aboutToQuit.connect(
    CurationDisplayDelegate.image_loader.shutdown
)
