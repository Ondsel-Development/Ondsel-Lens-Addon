# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import os
from datetime import datetime
import re

import json
import shutil
import requests
import uuid
import base64
import webbrowser
import logging
import random
import math

from inspect import cleandoc

import jwt
from jwt.exceptions import ExpiredSignatureError

from PySide import QtCore, QtGui, QtWidgets

import FreeCAD
import FreeCADGui as Gui
import AddonManager

import Utils

from DataModels import (
    WorkspaceListModel,
    CACHE_PATH,
    getBookmarkModel,
    ROLE_TYPE,
    TYPE_ORG,
    TYPE_BOOKMARK,
    ROLE_SHARE_MODEL_ID,
)
from VersionModel import OndselVersionModel
from LinkModel import ShareLinkModel
from APIClient import (
    APIClient,
    APIClientException,
    APIClientAuthenticationException,
    APIClientConnectionError,
    APIClientRequestException,
)
from Workspace import (
    WorkspaceModel,
    LocalWorkspaceModel,
    ServerWorkspaceModel,
    FileStatus,
)

from views.search_results_view import SearchResultsView

from PySide.QtGui import (
    QStyledItemDelegate,
    QStyle,
    QMessageBox,
    QApplication,
    QIcon,
    QAction,
    QActionGroup,
    QMenu,
    QSizePolicy,
    QPixmap,
    QListView,
)

from PySide.QtCore import QByteArray

from PySide.QtWidgets import QTreeView

from WorkspaceListDelegate import WorkspaceListDelegate


logger = Utils.getLogger(__name__)

MAX_LENGTH_BASE_FILENAME = 30
MAX_LENGTH_WORKSPACE_NAME = 33
ELLIPSES = "..."
MAX_INT32 = (1 << 31) - 1
CONFIG_PATH = FreeCAD.getUserConfigDir()
FILENAME_USER_CFG = "user.cfg"
FILENAME_SYS_CFG = "system.cfg"
PREFIX_PARAM_ROOT = "/Root/"

IDX_TAB_WORKSPACES = 0
IDX_TAB_BOOKMARKS = 1

PATH_BOOKMARKS = Utils.joinPath(CACHE_PATH, "bookmarks")

mw = Gui.getMainWindow()
p = FreeCAD.ParamGet("User parameter:BaseApp/Ondsel")

# Test server
# baseUrl = "https://ec2-54-234-132-150.compute-1.amazonaws.com"
# Prod server
baseUrl = "https://lens-api.ondsel.com/"
lensUrl = "https://lens.ondsel.com/"
ondselUrl = "https://www.ondsel.com/"

remote_changelog_url = (
    "https://github.com/Ondsel-Development/Ondsel-Lens/blob/master/changeLog.md"
)

remote_package_url = (
    "https://raw.githubusercontent.com/Ondsel-Development/"
    "Ondsel-Lens/master/package.xml"
)

try:
    import config

    baseUrl = config.base_url
    lensUrl = config.lens_url
except (ImportError, AttributeError):
    pass


class UpdateManager:
    def storePreferences(self):
        pref = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Addons")
        self.autocheck = pref.GetBool("AutoCheck")
        self.statusSelection = pref.GetInt("StatusSelection")
        self.packageTypeSelection = pref.GetInt("PackageTypeSelection")
        self.searchString = pref.GetString("SearchString")

    def setCustomPreferences(self):
        pref = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Addons")
        pref.SetBool("AutoCheck", True)
        pref.SetInt("StatusSelection", 3)
        pref.SetInt("PackageTypeSelection", 1)
        pref.SetString("SearchString", "Ondsel Lens")

    def restorePreferences(self):
        pref = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Addons")
        pref.SetBool("AutoCheck", self.autocheck)
        pref.SetInt("StatusSelection", self.statusSelection)
        pref.SetInt("PackageTypeSelection", self.packageTypeSelection)
        pref.SetString("SearchString", self.searchString)

    def openAddonManager(self, finishFunction):
        """Open the addon manager with custom preferences."""

        self.storePreferences()
        self.setCustomPreferences()

        addonManager = AddonManager.CommandAddonManager()
        addonManager.finished.connect(finishFunction)
        addonManager.Activated()


# Simple delegate drawing an icon and text
class FileListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the data for the current index
        if not index.isValid():
            return

        fileName, status, isFolder = index.data(
            WorkspaceModel.NameStatusAndIsFolderRole
        )

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        icon_rect = QtCore.QRect(option.rect.left(), option.rect.top(), 16, 16)
        text_rect = QtCore.QRect(
            option.rect.left() + 20,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height(),
        )
        if isFolder:
            icon = QtGui.QIcon.fromTheme("back", QtGui.QIcon(":/icons/folder.svg"))
        else:
            icon = QtGui.QIcon.fromTheme(
                "back", QtGui.QIcon(":/icons/document-new.svg")
            )
        icon.paint(painter, icon_rect)
        textToDisplay = renderFileName(fileName)
        if status:
            textToDisplay += " (" + str(status) + ")"

        fontMetrics = painter.fontMetrics()
        elidedText = fontMetrics.elidedText(
            textToDisplay, QtGui.Qt.ElideRight, option.rect.width()
        )
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, elidedText)


def renderFileName(fileName):
    base, extension = os.path.splitext(fileName)
    if len(base) > MAX_LENGTH_BASE_FILENAME:
        lengthSuffix = 5
        lengthEllipses = len(ELLIPSES)
        lengthPrefix = MAX_LENGTH_BASE_FILENAME - lengthSuffix - lengthEllipses
        return base[:lengthPrefix] + ELLIPSES + base[-lengthSuffix:] + extension
    else:
        return fileName


class LinkListDelegate(QStyledItemDelegate):
    iconShareClicked = QtCore.Signal(QtCore.QModelIndex)
    iconEditClicked = QtCore.Signal(QtCore.QModelIndex)
    iconDeleteClicked = QtCore.Signal(QtCore.QModelIndex)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        name = index.data(QtCore.Qt.DisplayRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        icon_copy_rect = QtCore.QRect(
            option.rect.right() - 60, option.rect.top(), 16, 16
        )
        icon_edit_rect = QtCore.QRect(
            option.rect.right() - 40, option.rect.top(), 16, 16
        )
        icon_delete_rect = QtCore.QRect(
            option.rect.right() - 20, option.rect.top(), 16, 16
        )
        text_rect = QtCore.QRect(
            option.rect.left() + 4,
            option.rect.top(),
            option.rect.width() - 60,
            option.rect.height(),
        )

        icon_copy = QtGui.QIcon.fromTheme("back", QtGui.QIcon(":/icons/edit-copy.svg"))
        icon_edit = QtGui.QIcon.fromTheme(
            "back", QtGui.QIcon(":/icons/Std_DlgParameter.svg")
        )
        icon_delete = QtGui.QIcon.fromTheme(
            "back", QtGui.QIcon(":/icons/edit_Cancel.svg")
        )

        icon_copy.paint(painter, icon_copy_rect)
        icon_edit.paint(painter, icon_edit_rect)
        icon_delete.paint(painter, icon_delete_rect)
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, name)

    def editorEvent(self, event, model, option, index):
        if not index.isValid():
            return False
        if (
            event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.LeftButton
        ):
            icon_share_rect = QtCore.QRect(
                option.rect.right() - 60, option.rect.top(), 16, 16
            )
            icon_edit_rect = QtCore.QRect(
                option.rect.right() - 40, option.rect.top(), 16, 16
            )
            icon_delete_rect = QtCore.QRect(
                option.rect.right() - 20, option.rect.top(), 16, 16
            )

            if icon_share_rect.contains(event.pos()):
                self.iconShareClicked.emit(index)
                return True
            elif icon_edit_rect.contains(event.pos()):
                self.iconEditClicked.emit(index)
                return True
            elif icon_delete_rect.contains(event.pos()):
                self.iconDeleteClicked.emit(index)
                return True
        # If the click wasn't on any icon, select the item as normal
        return super().editorEvent(event, model, option, index)


class BookmarkView(QTreeView):
    def drawBranches(self, painter, rect, index):
        pass


class BookmarkDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        type = index.data(ROLE_TYPE)
        if type == TYPE_ORG:
            name = index.data(QtCore.Qt.DisplayRole)

            # Mimick the workspaces list for consistency
            name_font = painter.font()
            name_font.setBold(True)

            # Draw the name
            name_rect = QtCore.QRect(
                option.rect.left() + 20,
                option.rect.top() + 10,
                option.rect.width() - 20,
                option.rect.height() // 2,
            )
            painter.setFont(name_font)
            painter.drawText(
                name_rect,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                name,
            )
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        type = index.data(ROLE_TYPE)
        if type == TYPE_ORG:
            return QtCore.QSize(100, 40)  # Adjust the desired width and height
        else:
            return super().sizeHint(option, index)


class WorkspaceView(QtWidgets.QScrollArea):

    def __init__(self):
        super(WorkspaceView, self).__init__(mw)

        self.current_workspace = None
        self.currentWorkspaceModel = None
        self.api = None

        self.setObjectName("workspaceView")
        self.form = Gui.PySideUic.loadUi(f"{Utils.mod_path}/WorkspaceView.ui")

        tabWidget = self.form.findChildren(QtGui.QTabWidget)[0]
        tabBar = tabWidget.tabBar()
        wsIcon = QtGui.QIcon(Utils.icon_path + "folder-multiple-outline.svg")
        tabBar.setTabIcon(0, wsIcon)
        bookmarkIcon = QtGui.QIcon(Utils.icon_path + "bookmark-outline.svg")
        tabBar.setTabIcon(1, bookmarkIcon)
        searchIcon = QtGui.QIcon(Utils.icon_path + "search.svg")
        tabBar.setTabIcon(2, searchIcon)
        # settingsIcon = QtGui.QIcon(Utils.icon_path + "settings.svg")
        # tabBar.setTabIcon(3, settingsIcon)

        self.setWidget(self.form)
        self.setWindowTitle("Ondsel Lens")

        self.createOndselButtonMenus()

        self.ondselIcon = QIcon(Utils.icon_path + "OndselWorkbench.svg")
        self.ondselIconOff = QIcon(Utils.icon_path + "OndselWorkbench-off.svg")
        self.form.userBtn.setIconSize(QtCore.QSize(32, 32))
        self.form.userBtn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.form.userBtn.clicked.connect(self.form.userBtn.showMenu)
        self.form.backToStartBtn.hide()

        self.form.buttonBack.clicked.connect(self.backClicked)

        self.workspacesModel = WorkspaceListModel(api=self.api)
        self.workspacesDelegate = WorkspaceListDelegate(self)
        self.form.workspaceListView.setModel(self.workspacesModel)
        self.form.workspaceListView.setItemDelegate(self.workspacesDelegate)
        self.form.workspaceListView.doubleClicked.connect(self.enterWorkspace)
        self.form.workspaceListView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.workspaceListView.customContextMenuRequested.connect(
            self.showWorkspaceContextMenu
        )
        self.workspacesModel.rowsInserted.connect(self.switchView)
        self.workspacesModel.rowsRemoved.connect(self.switchView)

        self.filesDelegate = FileListDelegate(self)
        self.form.fileList.setItemDelegate(self.filesDelegate)
        self.form.fileList.doubleClicked.connect(self.fileListDoubleClicked)
        self.form.fileList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.fileList.customContextMenuRequested.connect(self.showFileContextMenu)
        self.form.fileList.clicked.connect(self.fileListClicked)

        self.form.versionsComboBox.activated.connect(self.versionClicked)

        self.linksDelegate = LinkListDelegate(self)
        self.linksDelegate.iconShareClicked.connect(self.shareShareLinkClicked)
        self.linksDelegate.iconEditClicked.connect(self.editShareLinkClicked)
        self.linksDelegate.iconDeleteClicked.connect(self.deleteShareLinkClicked)
        self.form.linksView.setItemDelegate(self.linksDelegate)
        self.form.linksView.doubleClicked.connect(self.linksListDoubleClicked)
        self.form.linksView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.linksView.customContextMenuRequested.connect(
            self.showLinksContextMenu
        )

        self.form.addLinkBtn.clicked.connect(self.addShareLink)

        addFileMenu = QtGui.QMenu(self.form.addFileBtn)
        addFileAction = QtGui.QAction("Add current file", self.form.addFileBtn)
        addFileAction.triggered.connect(self.addCurrentFile)
        addFileMenu.addAction(addFileAction)
        addFileAction2 = QtGui.QAction("Select files...", self.form.addFileBtn)
        addFileAction2.triggered.connect(self.addSelectedFiles)
        addFileMenu.addAction(addFileAction2)
        addFileAction3 = QtGui.QAction("Add a directory", self.form.addFileBtn)
        addFileAction3.triggered.connect(self.addDir)
        addFileMenu.addAction(addFileAction3)
        self.form.addFileBtn.setMenu(addFileMenu)

        self.form.viewOnlineBtn.clicked.connect(self.openModelOnline)
        self.form.makeActiveBtn.clicked.connect(self.makeActive)

        self.form.fileDetails.setVisible(False)

        explainText = cleandoc(
            """
            <h1 style="text-align:center; font-weight:bold;">Welcome</h1>

            <p>You're not currently logged in to the Ondsel service. Use the button
               above to log in or create an account. When you log in, this space will
               show your workspaces.
            </p>

            <p>You can enter the workspaces by double-clicking them.</p>

            <p>Each workspace is a collection of files. Think of it like a project.</p>
            """
        )

        self.form.txtExplain.setHtml(explainText)
        self.form.txtExplain.setReadOnly(True)
        self.form.txtExplain.hide()

        self.initializeBookmarks()

        # initialize search
        self.form.searchResultScrollArea = SearchResultsView(self)
        self.form.searchResultFrame.layout().addWidget(self.form.searchResultScrollArea)

        self.initializeUpdateLens()

        self.try_login()
        self.switchView()

        def tryRefresh():
            self.workspacesModel.refreshModel()

            # Set a timer to check regularly the server
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.timerTick)
            self.timer.setInterval(60000)
            self.timer.start()

        self.handle(tryRefresh)
        self.handleRequest(self.check_for_update)

        # linksView.setModel(self.linksModel)

    def initializeBookmarks(self):
        tabWidget = self.form.tabWidget
        self.form.viewBookmarks = BookmarkView(tabWidget)
        bookmarkView = self.form.viewBookmarks
        self.form.tabBookmarks.layout().addWidget(bookmarkView)

        tabWidget.currentChanged.connect(self.onTabChanged)
        tabWidget.setTabToolTip(
            IDX_TAB_WORKSPACES,
            "Explore and create 3D CAD designs in your Lens workspaces",
        )
        tabWidget.setTabToolTip(IDX_TAB_BOOKMARKS, "Explore your Lens bookmarks")
        bookmarkView.setRootIsDecorated(False)
        bookmarkView.setToolTip("Bookmarks per organization")
        bookmarkView.setExpandsOnDoubleClick(False)
        bookmarkView.header().hide()
        bookmarkView.setItemDelegate(BookmarkDelegate())
        bookmarkView.doubleClicked.connect(self.bookmarkDoubleClicked)
        bookmarkView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        bookmarkView.customContextMenuRequested.connect(self.showBookmarkContextMenu)

    def initializeUpdateLens(self):
        self.form.frameUpdate.hide()
        self.form.updateBtn.clicked.connect(self.openAddonManager)

    def openAddonManager(self):
        self.updateManager = UpdateManager()
        self.updateManager.openAddonManager(self.addonManagerFinished)

    def addonManagerFinished(self):
        self.updateManager.restorePreferences()
        self.UpdateManager = None

    # def generate_expired_token(self):
    #     # generate an expired token for testing
    #     # Set expiration time to 5 minutes ago
    #     expiration_time = datetime.now() - timedelta(minutes=5)
    #     payload = {
    #         "exp": expiration_time.timestamp(),
    #         # Add other claims as needed
    #     }
    #     secret_key = "your_secret_key"  # Replace with your secret key
    #     token = jwt.encode(payload, secret_key, algorithm="HS256")
    #     return token

    def createOndselButtonMenus(self):
        # Ondsel Button's menu when logged in
        self.userMenu = QMenu(self.form.userBtn)
        userActions = QActionGroup(self.userMenu)

        a = QAction("Visit Ondsel Lens", userActions)
        a.triggered.connect(self.ondselAccount)
        self.userMenu.addAction(a)

        # self.synchronizeAction = QAction("Synchronize", userActions)
        # self.synchronizeAction.setVisible(False)
        # self.userMenu.addAction(self.synchronizeAction)

        # Prefer to do this in the dashboard
        # self.newWorkspaceAction = QAction("Add new workspace", userActions)
        # self.newWorkspaceAction.triggered.connect(self.newWorkspaceBtnClicked)
        # self.userMenu.addAction(self.newWorkspaceAction)

        # Settings
        submenuSettings = QMenu("Settings", self.userMenu)
        clearCacheAction = QAction("Clear Cache on logout", submenuSettings)
        clearCacheAction.setCheckable(True)
        clearCacheAction.setChecked(p.GetBool("clearCache", False))
        clearCacheAction.triggered.connect(lambda state: p.SetBool("clearCache", state))
        submenuSettings.addAction(clearCacheAction)
        self.userMenu.addMenu(submenuSettings)

        submenuPrefs = QMenu("Preferences", self.userMenu)
        downloadOnselPrefsAction = QAction(
            "Download Ondsel ES default preferences", submenuPrefs
        )
        downloadOnselPrefsAction.setEnabled(FreeCAD.ConfigGet("ExeVendor") == "Ondsel")
        downloadOnselPrefsAction.triggered.connect(self.downloadOndselDefaultPrefs)
        submenuPrefs.addAction(downloadOnselPrefsAction)
        self.userMenu.addMenu(submenuPrefs)

        a4 = QAction("Log out", userActions)
        a4.triggered.connect(self.logout)
        self.userMenu.addAction(a4)

        # Ondsel Button's menu when user not logged in
        self.guestMenu = QMenu(self.form.userBtn)
        guestActions = QActionGroup(self.guestMenu)

        a5 = QAction("Login", guestActions)
        a5.triggered.connect(self.login_btn_clicked)
        self.guestMenu.addAction(a5)

        a6 = QAction("Sign up", guestActions)
        a6.triggered.connect(self.showOndselSignUpPage)
        self.guestMenu.addAction(a6)

        # self.guestMenu.addAction(self.newWorkspaceAction)

    # ####
    # Authentication
    # ####

    def is_logged_in(self):
        """Whether a user is logged in.

        The user may be disconnected.
        """
        return self.api is not None and self.api.is_logged_in()

    def is_connected(self):
        """Whether a user is connected.

        This implies that the user is logged in.
        """
        return self.api is not None and self.api.is_connected()

    def try_login(self):
        # Check if user is already logged in.
        login_data_str = p.GetString("loginData", "")
        if login_data_str != "":
            login_data = json.loads(login_data_str)
            access_token = login_data["accessToken"]
            # access_token = self.generate_expired_token()

            if self.is_token_expired(access_token):
                self.logout()
            else:
                user = login_data["user"]
                self.set_ui_logged_in(True, user)

                if self.api is None:
                    self.api = APIClient(
                        "",
                        "",
                        baseUrl,
                        lensUrl,
                        self.get_source(),
                        self.get_version(),
                        access_token,
                        user,
                    )

                # Set a timer to logout when token expires.
                # we know that the token is not expired
                self.set_token_expiration_timer(access_token)
        else:
            self.set_ui_logged_in(False)

    def login_btn_clicked(self):
        while True:
            # Show a login dialog to get the user's email and password
            dialog = LoginDialog()
            if dialog.exec() == QtGui.QDialog.Accepted:
                email, password = dialog.get_credentials()
                try:
                    self.api = APIClient(
                        email,
                        password,
                        baseUrl,
                        lensUrl,
                        self.get_source(),
                        self.get_version(),
                    )
                    self.workspacesModel.set_api(self.api)
                    self.api.authenticate()
                except APIClientAuthenticationException as e:
                    logger.warn(e)
                    continue  # Present the login dialog again if authentication fails
                except APIClientException as e:
                    logger.error(e)
                    self.api = None
                    self.workspacesModel.set_api(None)
                    break
                # Check if the request was successful (201 status code)
                if self.api.access_token is not None:
                    loginData = {
                        "accessToken": self.api.access_token,
                        "user": self.api.user,
                    }
                    p.SetString("loginData", json.dumps(loginData))

                    self.set_ui_logged_in(True, self.api.user)
                    self.leaveWorkspace()
                    self.handle(self.workspacesModel.refreshModel)
                    self.switchView()

                    # Set a timer to logout when token expires.  since we've
                    # just received the access token, it is very unlikely that
                    # it is expired.
                    self.set_token_expiration_timer(self.api.access_token)
                else:
                    logger.warn("Authentication failed")
                break
            else:
                break  # Exit the login loop if the dialog is canceled

    def disconnect(self):
        self.set_ui_disconnected()
        self.api.disconnect()
        if self.currentWorkspaceModel:
            self.setWorkspaceModel()

        self.hideFileDetails()

    def logout(self):
        self.set_ui_logged_in(False)
        p.SetString("loginData", "")
        self.api.logout()

        if self.currentWorkspaceModel:
            self.setWorkspaceModel()

        self.hideFileDetails()

        if p.GetBool("clearCache", False):
            shutil.rmtree(CACHE_PATH)
            self.current_workspace = None
            self.currentWorkspaceModel = None
            self.form.fileList.setModel(None)
            self.workspacesModel.removeWorkspaces()
            self.switchView()
            self.form.workspaceNameLabel.setText("")
            self.form.fileDetails.setVisible(False)

    def is_token_expired(self, token):
        try:
            expiration_time = self.get_token_expiration_time(token)
        except ExpiredSignatureError:
            return True
        current_time = datetime.now()
        return current_time > expiration_time

    def set_token_expiration_timer(self, token):
        # Should be called when there is no risk for an expired signature
        # However, the code still handles the error gracefully.
        try:
            expiration_time = self.get_token_expiration_time(token)
            current_time = datetime.now()

            time_difference = expiration_time - current_time
            interval_milliseconds = max(0, time_difference.total_seconds() * 1000)
            if interval_milliseconds < MAX_INT32:
                # Create a QTimer that triggers only once when the token is expired
                self.token_timer = QtCore.QTimer()
                self.token_timer.setSingleShot(True)
                self.token_timer.timeout.connect(self.token_expired_handler)
                self.token_timer.start(interval_milliseconds)
        except ExpiredSignatureError as e:
            # unexpected
            self.logout()
            self.set_ui_logged_in(False)
            logger.error(e)

    def token_expired_handler(self):
        QMessageBox.information(
            None,
            "Token Expired",
            "Your authentication token has expired, you have been logged out.",
        )

        self.logout()

    def get_token_expiration_time(self, token):
        """Get a token expiration time.

        Should be called only when we assume that the token is not expired.

        Otherwise we log out and raise the exception again.  In case another
        exception happens, we do the same.
        """

        try:
            decoded_token = jwt.decode(
                token,
                audience="lens.ondsel.com",
                options={"verify_signature": False, "verify_aud": False},
            )
        except ExpiredSignatureError as e:
            raise e
        except Exception as e:
            self.logout()

            self.set_ui_logged_in(False)
            logger.error(e)
            raise e
        return datetime.fromtimestamp(decoded_token["exp"])

    def set_ui_disconnected(self):
        self.form.userBtn.setText(self.api.getNameUser() + " (disconnected)")

    def set_ui_connected(self):
        logger.debug("set_ui_connected")
        self.form.userBtn.setText(self.api.getNameUser())

    def set_ui_logged_in(self, loggedIn, user=None):
        """Toggle the visibility of UI elements based on if user is logged in"""

        logger.debug("set_ui_logged_in")
        if loggedIn:
            userBtnText = ""
            if "name" in user:
                userBtnText = user["name"]

            self.form.userBtn.setText(userBtnText)
            self.form.userBtn.setIcon(self.ondselIcon)
            self.form.userBtn.setMenu(self.userMenu)
        else:
            self.form.userBtn.setText("Local")
            self.form.userBtn.setIcon(self.ondselIconOff)
            self.form.userBtn.setMenu(self.guestMenu)

    def enterWorkspace(self, index):
        logger.debug("entering workspace")
        self.current_workspace = self.workspacesModel.data(index)
        self.setWorkspaceModel()

    def setWorkspaceModel(self):
        if self.is_connected():
            logger.debug("connected")
            # not necessary to set the path because we will start with the list
            # of workspaces.
            self.currentWorkspaceModel = ServerWorkspaceModel(
                self.current_workspace, apiClient=self.api
            )
        else:
            logger.debug("not connected")
            subPath = ""
            if hasattr(self, "currentWorkspaceModel") and self.currentWorkspaceModel:
                subPath = self.currentWorkspaceModel.subPath
            self.currentWorkspaceModel = LocalWorkspaceModel(
                self.current_workspace, subPath=subPath
            )

        # Create a workspace model and set it to the list
        # if self.api is None and self.access_token is None:
        #     logger.debug("You need to login first")
        #     self.login_btn_clicked()
        #     self.enterWorkspace(index)
        #     return
        # if self.api is None and self.access_token is not None:
        #     self.api = APIClient(
        #         "", "", baseUrl, lensUrl, self.access_token, self.user
        #     )

        #     self.currentWorkspaceModel = ServerWorkspaceModel(
        #         self.current_workspace, API_Client=self.api
        #     )
        # else:
        #     self.currentWorkspaceModel = LocalWorkspaceModel(self.current_workspace)

        self.setWorkspaceNameLabel()

        self.form.fileList.setModel(self.currentWorkspaceModel)
        # self.synchronizeAction.triggered.connect(
        #     self.currentWorkspaceModel.refreshModel
        # )
        # self.newWorkspaceAction.setVisible(False)

        self.switchView()

    def leaveWorkspace(self):
        if self.current_workspace is None:
            return
        # self.newWorkspaceAction.setVisible(True)
        # self.synchronizeAction.setVisible(False)
        # self.synchronizeAction.triggered.disconnect()
        self.current_workspace = None
        self.currentWorkspaceModel = None
        self.form.fileList.setModel(None)
        self.handle(self.workspacesModel.refreshModel)
        self.switchView()
        self.form.workspaceNameLabel.setText("")
        self.form.fileDetails.setVisible(False)

    def switchView(self):
        isFileView = self.current_workspace is not None

        if isFileView:
            self.form.workspaceListView.setVisible(False)
            self.form.WorkspaceDetails.setVisible(True)
            self.form.fileList.setVisible(True)
            self.form.fileList.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding
            )
        else:
            self.form.WorkspaceDetails.setVisible(False)
            self.form.fileList.setVisible(False)
            if self.is_logged_in() and self.workspacesModel.rowCount() == 0:
                # the user may be disconnected
                self.form.txtExplain.setVisible(True)
            else:
                self.form.txtExplain.setVisible(False)
                self.form.workspaceListView.setVisible(True)

    def backClicked(self):
        if self.current_workspace is None:
            return
        subPath = self.currentWorkspaceModel.subPath

        if subPath == "":
            self.leaveWorkspace()
        else:

            def tryOpenParent():
                self.currentWorkspaceModel.openParentFolder()
                self.setWorkspaceNameLabel()
                self.hideFileDetails()

            self.handle(tryOpenParent)

    def handleRequest(self, func):
        """Handle a function that raises an exception from requests.

        Issue warning/errors and possibly log out the user, making
        it still possible to use the addon.
        """
        try:
            func()
        except requests.exceptions.RequestException as e:
            logger.debug(e)

    def handle(self, func):
        """Handle a function that raises an APICLientException.

        Issue warning/errors and possibly log out the user, making
        it still possible to use the addon.

        If the user is disconnected before the call, we simply try the call but
        ignore any warning if it doesn't succeed.  If the call succeeds but we
        were not connected, it means we are connected again, so we set the UI
        to be connected.

        Returns true if the user is disconnected

        """
        connected_before_call = self.is_connected()
        try:
            func()
            if not connected_before_call:
                # since the call succeeds, it may mean we are connected again
                if self.is_connected():
                    # check if we are connected right now
                    logger.info("The connection to the Lens service is restored.")
                    self.set_ui_connected()
            return False
        except APIClientConnectionError as e:
            if connected_before_call:
                if logger.level <= logging.DEBUG:
                    logger.warn(e)
                else:
                    logger.warn("Disconnected from the Lens service.")
                self.disconnect()
        except APIClientRequestException as e:
            if connected_before_call:
                if logger.level <= logging.DEBUG:
                    logger.warn(e)
                else:
                    logger.warn("Disconnected from the Lens service.")
                self.disconnect()
        except APIClientAuthenticationException as e:
            logger.warn(e)
            logger.warn("Logging out")
            self.logout()
        except APIClientException as e:
            logger.error("Uncaught exception:")
            logger.error(e)
            logger.warn("Logging out")
            self.logout()
        return True

    def tryOpenPathFile(self, pathFile):
        if Utils.isOpenableByFreeCAD(pathFile):
            logger.debug(f"Opening file: {pathFile}")
            if not self.restoreFile(pathFile):
                FreeCAD.loadFile(pathFile)
        else:
            logger.warn(f"FreeCAD cannot open {pathFile}")

    def openFile(self, index):
        """Open a file

        throws an APIClientException
        """
        wsm = self.currentWorkspaceModel
        fileItem = wsm.data(index)
        if fileItem.is_folder:
            wsm.openDirectory(index)
        else:
            pathFile = Utils.joinPath(wsm.getFullPath(), fileItem.name)
            if not os.path.isfile(pathFile) and self.is_connected():
                wsm.downloadFile(fileItem)
                # wsm has refreshed
            self.tryOpenPathFile(pathFile)

    def setWorkspaceNameLabel(self):
        wsm = self.currentWorkspaceModel
        workspacePath = wsm.getWorkspacePath()
        if len(workspacePath) > MAX_LENGTH_WORKSPACE_NAME:
            lengthPrefix = (MAX_LENGTH_WORKSPACE_NAME - len(ELLIPSES)) // 2
            lengthSuffix = lengthPrefix
            workspacePath = (
                workspacePath[:lengthPrefix] + ELLIPSES + workspacePath[-lengthSuffix:]
            )
        self.form.workspaceNameLabel.setText(workspacePath)

    def fileListDoubleClicked(self, index):
        def tryOpenFile():
            self.openFile(index)
            self.setWorkspaceNameLabel()

        self.handle(tryOpenFile)

    def linksListDoubleClicked(self, index):
        model = self.form.linksView.model()
        linkData = model.data(index, ShareLinkModel.EditLinkRole)

        dialog = SharingLinkEditDialog(linkData, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()
            self.handle(lambda: model.update_link(index, link_properties))

    # ####
    # Downloading files
    # ####

    def confirmFileTransfer(self, message, transferMessage):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirmation")
        msg_box.setText(
            f"{message} {transferMessage}\nAre you sure you want to proceed?"
        )
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        return msg_box.exec_() == QMessageBox.Yes

    def confirmDownload(self, message):
        return self.confirmFileTransfer(
            message, "Downloading will override this local version."
        )

    def downloadFileIndex(self, index):
        wsm = self.currentWorkspaceModel
        file_item = wsm.files[index.row()]
        self.downloadFileFileItem(file_item)

    def downloadVersionConfirm(self, fileItem, version):
        """Download a version after asking confirmation.

        Refreshes the workspace model in any case.
        """
        wsm = self.currentWorkspaceModel
        if fileItem.status == FileStatus.LOCAL_COPY_OUTDATED:
            msg = "The local copy is outdated compared to the active version."
            if not self.confirmDownload(msg):
                wsm.refreshModel()
                return False
        elif fileItem.status == FileStatus.UNTRACKED:
            # should not happen as the menu should not be enabled
            logger.error("It is not possible to download an untracked file")
            return False
        elif fileItem.status == FileStatus.SERVER_COPY_OUTDATED:
            msg = "The local copy is newer than the active version."
            if not self.confirmDownload(msg):
                wsm.refreshModel()
                return False

        return wsm.downloadVersion(fileItem, version)

    def downloadVersion(self, fileItem, version):
        """Download a version.

        Refreshes the workspace model in any case.
        """
        comboBox = self.form.versionsComboBox
        versionModel = comboBox.model()
        wsm = self.currentWorkspaceModel

        # if the current file is already a version, then simply download
        if versionModel.getOnDiskVersionId(fileItem):
            return wsm.downloadVersion(fileItem, version)
        else:
            return self.downloadVersionConfirm(fileItem, version)

    def downloadFileFileItem(self, fileItem):
        """Download a file based on a fileItem.

        Refreshes the wsm in any case.
        """
        wsm = self.currentWorkspaceModel
        if fileItem.status == FileStatus.LOCAL_COPY_OUTDATED:
            msg = "The local copy is outdated compared to the active version."
            if not self.confirmDownload(msg):
                wsm.refreshModel()
                return
        elif fileItem.status == FileStatus.UNTRACKED:
            # should not happen as the menu should not be enabled
            logger.error("It is not possible to download an untracked file")
            return
        elif fileItem.status == FileStatus.SERVER_COPY_OUTDATED:
            msg = "The local copy is newer than the active version."
            if not self.confirmDownload(msg):
                wsm.refreshModel()
                return
        elif fileItem.status == FileStatus.SYNCED:
            logger.info("This file is already in sync")
            wsm.refreshModel()
            return
        wsm.downloadFile(fileItem)
        if Utils.isOpenableByFreeCAD(fileItem.getPath()):
            self.updateThumbnail(fileItem)

    def restoreFile(self, pathFile):
        # iterate over the files
        for doc in FreeCAD.listDocuments().values():
            if doc.FileName == pathFile:
                doc.restore()
                return True
        return False

    def versionClicked(self, row):
        comboBox = self.form.versionsComboBox

        versionModel = comboBox.model()
        indexVersion = versionModel.index(row, 0)

        version = versionModel.data(indexVersion, role=QtCore.Qt.UserRole)
        versionId = version["_id"]
        wsm = self.currentWorkspaceModel

        fileItem = versionModel.fileItem

        def refreshUI():
            # assumes that wsm has refreshed
            newFileItem = wsm.getFileItemFileId(fileItem.serverFileDict["_id"])
            versionModel.refreshModel(newFileItem)
            comboBox.setCurrentIndex(versionModel.getCurrentIndex())
            self.form.makeActiveBtn.setVisible(versionModel.canBeMadeActive())
            return newFileItem

        def trySetVersion():
            if versionId == versionModel.onDiskVersionId:
                logger.info("This version has already been downloaded")
            else:
                # the download will refresh the wsm, so refresh the UI
                if self.downloadVersion(fileItem, version):
                    refreshedFileItem = refreshUI()
                    self.restoreFile(refreshedFileItem.getPath())
                    self.updateThumbnail(refreshedFileItem)
                else:
                    refreshUI()

        self.handle(trySetVersion)

    def updateThumbnail(self, fileItem):
        fileName = fileItem.name
        path = self.currentWorkspaceModel.getFullPath()
        pixmap = Utils.extract_thumbnail(f"{path}/{fileName}")
        if pixmap is None:
            modelId = fileItem.getModelId()
            if modelId:
                pixmap = self.getServerThumbnail(fileName, path, modelId)
                if pixmap is None:
                    pixmap = QPixmap(f"{Utils.mod_path}/Resources/thumbTest.png")
        self.form.thumbnail_label.setFixedSize(pixmap.width(), pixmap.height())
        self.form.thumbnail_label.setPixmap(pixmap)

    def fileListClickedConnected(self, file_item):
        fileName = file_item.name
        modelId = file_item.getModelId()
        # if file_item.serverFileDict and "modelId" in file_item.serverFileDict:
        #     # currentModelId is used for the server model and is necessary to
        #     # open models online
        #     self.currentModelId = file_item.serverFileDict["modelId"]
        self.updateThumbnail(file_item)
        self.form.fileNameLabel.setText(renderFileName(fileName))

        version_model = None
        self.links_model = None

        self.form.fileList.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.form.fileDetails.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )
        self.form.thumbnail_label.show()
        self.form.fileNameLabel.show()
        self.form.fileDetails.setVisible(True)

        # It seems an idea to have the values below as default to then set them when
        # initializing the models succeeds.  However, this leads to a jumping file list,
        # so the nested function below is a better option, using it wherever we need to
        # turn it off.
        def hideDetails():
            self.form.viewOnlineBtn.setVisible(False)
            self.form.linkDetails.setVisible(False)
            self.form.makeActiveBtn.setVisible(False)

        if modelId is not None:

            def tryInitModels():
                self.links_model = ShareLinkModel(modelId, self.api)
                nonlocal version_model
                version_model = OndselVersionModel(modelId, self.api, file_item)
                self.form.viewOnlineBtn.setVisible(True)
                self.form.linkDetails.setVisible(True)
                self.form.makeActiveBtn.setVisible(version_model.canBeMadeActive())

            if self.handle(tryInitModels):
                # disconnected
                hideDetails()
        else:
            hideDetails()

        self.form.linksView.setModel(self.links_model)
        self.setVersionListModel(version_model)

    def hideFileDetails(self):
        """Hide all the links/thumbnails/etc"""
        self.form.thumbnail_label.hide()
        self.form.fileNameLabel.hide()
        self.form.viewOnlineBtn.setVisible(False)
        self.form.makeActiveBtn.setVisible(False)
        self.form.linkDetails.setVisible(False)
        self.form.fileDetails.setVisible(False)
        self.form.fileList.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def fileListClickedDisconnected(self, fileName):
        path = self.currentWorkspaceModel.getFullPath()
        pixmap = Utils.extract_thumbnail(f"{path}/{fileName}")
        if pixmap:
            self.form.thumbnail_label.show()
            self.form.thumbnail_label.setFixedSize(pixmap.width(), pixmap.height())
            self.form.thumbnail_label.setPixmap(pixmap)
            self.form.fileNameLabel.setText(renderFileName(fileName))
            self.form.fileNameLabel.show()
            self.form.viewOnlineBtn.setVisible(False)
            self.form.makeActiveBtn.setVisible(False)
            self.form.linkDetails.setVisible(False)
            self.form.fileDetails.setVisible(True)
            self.form.linksView.setModel(None)
            self.setVersionListModel(None)

    def fileListClicked(self, index):
        # This function is also executed once in case of a double click. It is best to
        # do as little modifications to the state as possible.
        file_item = self.currentWorkspaceModel.data(index)
        fileName = file_item.name
        # self.currentModelId = None
        if Utils.isOpenableByFreeCAD(file_item.getPath()):
            if self.is_connected():
                self.fileListClickedConnected(file_item)
            else:
                self.fileListClickedDisconnected(fileName)
        else:
            self.hideFileDetails()

    def getServerThumbnail(self, fileName, path, fileId):
        # check if we have stored the thumbnail locally already.
        if not os.path.exists(f"{path}/.thumbnails"):
            os.makedirs(f"{path}/.thumbnails")
        localThumbPath = f"{path}/.thumbnails/{fileName}.png"
        if os.path.exists(localThumbPath):
            pixmap = QPixmap(localThumbPath)
        else:
            pixmap = self.currentWorkspaceModel.getServerThumbnail(fileId)
            if pixmap is not None:
                pixmap.save(localThumbPath, "PNG")
        return pixmap

    def setVersionListModel(self, model):
        if model is None:
            self.form.versionsComboBox.clear()
            emptyModel = QtCore.QStringListModel()
            self.form.versionsComboBox.setModel(emptyModel)
            self.form.versionsComboBox.setVisible(False)
        else:
            self.form.versionsComboBox.setModel(model)
            self.form.versionsComboBox.setCurrentIndex(model.getCurrentIndex())
            self.form.versionsComboBox.setVisible(True)

    # workspace add and delete is preferred to do in the Dashboard
    # def showWorkspaceContextMenu(self, pos):
    #     index = self.form.workspaceListView.indexAt(pos)

    #     if index.isValid():
    #         menu = QtGui.QMenu()

    #         deleteAction = menu.addAction("Delete")
    #         deleteAction.setEnabled(self.api is not None)

    #         action = menu.exec_(
    #             self.form.workspaceListView.viewport().mapToGlobal(pos)
    #         )

    #         if action == deleteAction:
    #             result = QtGui.QMessageBox.question(
    #                 self,
    #                 "Delete Workspace",
    #                 "Are you sure you want to delete this workspace?",
    #                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
    #             )
    #             if result == QtGui.QMessageBox.Yes:
    #                 self.api.deleteWorkspace(
    #                     self.workspacesModel.data(index)["_id"]
    #                 )
    #                 self.workspacesModel.refreshModel()
    #     else:
    #         menu = QtGui.QMenu()
    #         addAction = menu.addAction("Add workspace")
    #         addAction.setEnabled(self.api is not None)

    #         action = menu.exec_(
    #             self.form.workspaceListView.viewport().mapToGlobal(pos)
    #         )

    #         if action == addAction:
    #             self.newWorkspaceBtnClicked()

    # ####
    # Managing preferences
    # ####

    def showWorkspaceContextMenu(self, pos):
        def getOrganizationName(index):
            workspaceData = self.workspacesModel.data(index)
            organizationData = workspaceData.get("organization")
            if organizationData:
                return organizationData.get("name")

        index = self.form.workspaceListView.indexAt(pos)

        if index.isValid():
            menu = QtGui.QMenu()

            nameOrganization = getOrganizationName(index)

            if nameOrganization:
                labelMenuBase = f"preferences for {nameOrganization}"

                storePrefAction = menu.addAction(f"Upload {labelMenuBase}")
                storePrefAction.setEnabled(self.is_connected())

                loadPrefAction = menu.addAction(f"Download {labelMenuBase}")
                loadPrefAction.setEnabled(self.is_connected())

                action = menu.exec_(
                    self.form.workspaceListView.viewport().mapToGlobal(pos)
                )

                if action == storePrefAction:
                    self.storePrefs(index)
                elif action == loadPrefAction:
                    self.loadPrefsOrg(index)

    def uploadPrefs(self, pathConfig):
        base, extension = os.path.splitext(pathConfig)
        uniqueName = f"{str(uuid.uuid4())}{extension}"

        self.api.uploadFileToServer(uniqueName, pathConfig)

        return uniqueName

    def storePrefs(self, index):
        workspaceData = self.workspacesModel.data(index)
        orgData = workspaceData.get("organization")
        orgId = orgData["_id"]

        pathUserConfig = Utils.joinPath(CONFIG_PATH, FILENAME_USER_CFG)
        pathSysConfig = Utils.joinPath(CONFIG_PATH, FILENAME_SYS_CFG)

        def tryStorePrefs():
            uniqueNameUserConfig = self.uploadPrefs(pathUserConfig)
            uniqueNameSysConfig = self.uploadPrefs(pathSysConfig)

            self.api.uploadPrefs(
                orgId,
                uniqueNameUserConfig,
                FILENAME_USER_CFG,
                uniqueNameSysConfig,
                FILENAME_SYS_CFG,
            )

        self.handle(tryStorePrefs)

    def convertParam(self, type, paramGroup, value):
        if type == "FCBool":
            return paramGroup.GetBool, paramGroup.SetBool, bool(int(value))
        elif type == "FCUInt":
            return paramGroup.GetUnsigned, paramGroup.SetUnsigned, int(value)
        elif type == "FCInt":
            return paramGroup.GetInt, paramGroup.SetInt, int(value)
        elif type == "FCFloat":
            return paramGroup.GetFloat, paramGroup.SetFloat, float(value)
        elif type == "FCText":
            return paramGroup.GetString, paramGroup.SetString, value
        else:
            logger.error("Unknown parameter type")
            return None, None, None

    def getRemoveFunc(self, type, paramGroup):
        if type == "Boolean":
            return paramGroup.RemBool
        elif type == "Unsigned Long":
            return paramGroup.RemUnsigned
        elif type == "Integer":
            return paramGroup.RemInt
        elif type == "Float":
            return paramGroup.RemFloat
        elif type == "String":
            return paramGroup.RemString
        else:
            logger.error("Unknown parameter type")
            return None

    def getTypeParamGroup(self, group, param):
        contents = group.GetContents()
        if contents:
            filtered_tuples = filter(
                lambda tup: len(tup) > 1 and tup[1] == param, contents
            )
            result = list(filtered_tuples)
            if result:
                return result[0][0]

        return None

    def removeParam(self, group, param, path):
        type = self.getTypeParamGroup(group, param)
        if type:
            removeFunc = self.getRemoveFunc(type, group)
            removeFunc(param)
            logger.info(f"Removing parameter '{param}' in group '{path}'")

    def setPreference(self, param, path, value, setFunc):
        logger.info(f"Setting parameter '{param}' " f"in group '{path}' to '{value}'")
        setFunc(param, value)
        # The code below does not succeed in getting the task panel at the
        # right location.
        # if (
        #     param == "MainWindowState"
        #     and path == "User parameter:BaseApp/Preferences/MainWindow"
        # ):
        #     logger.debug("Restoring the window state")
        #     mw.restoreState(QByteArray(base64.b64decode(value)))

    def setPrefPath(self, path, param, type, value):
        paramGroup = FreeCAD.ParamGet(path)

        if type == "KeyNotFound":
            self.removeParam(paramGroup, param, path)
        else:
            getFunc, setFunc, convertedValue = self.convertParam(
                type, paramGroup, value
            )
            currentValue = getFunc(param)
            if currentValue != convertedValue:
                self.setPreference(param, path, convertedValue, setFunc)

    def setPrefsFile(self, prefsFile):
        fileName = prefsFile["fileName"]
        if fileName == FILENAME_USER_CFG:
            prefix = "User parameter:"
        elif fileName == FILENAME_SYS_CFG:
            prefix = "System parameter:"
        else:
            logger.error("Unknown preference file")
            return

        for prefData in prefsFile["data"]:
            key, type, value = prefData["key"], prefData["type"], prefData["value"]
            # discard the prefix '/Root/' and split into path values
            pathValues = key[len(PREFIX_PARAM_ROOT) :].split("/")
            # the last path value is the parameter of interest
            param = pathValues[-1]
            # the path is the prefix and the rest of the pathvalues joined together
            path = prefix + "/".join(pathValues[:-1])
            self.setPrefPath(path, param, type, value)

    def setPrefs(self, prefs):
        for filePrefs in prefs["currentVersion"]["files"]:
            self.setPrefsFile(filePrefs)

    def restartFreecad(self, mainWindowState):
        """Shuts down and restarts FreeCAD"""

        # Very similar to how the Addon Manager restarts FreeCAD

        args = QtWidgets.QApplication.arguments()[1:]
        # delay restoring the window state as much as possible to make sure
        # that the panels are at the right location
        mw.restoreState(mainWindowState)
        if mw.close():
            QtCore.QProcess.startDetached(
                QtWidgets.QApplication.applicationFilePath(), args
            )

    def askRestart(self, backupFiles, windowState):
        # similar to the question from the Addon Manager
        m = QtWidgets.QMessageBox()
        m.setWindowTitle("Ondsel Lens")
        m.setWindowIcon(QtGui.QIcon(":/icons/OndselWorkbench.svg"))
        m.setWindowIcon(self.ondselIcon)
        m.setTextFormat(QtCore.Qt.RichText)
        restartMessage = "You must restart FreeCAD for changes to take effect."
        if backupFiles:
            m.setText(
                "The current preferences have been backed up in:"
                "<ul>"
                f"<li>{backupFiles[0]}</li>"
                f"<li>{backupFiles[1]}</li>"
                "</ul>"
                "<br>"
                f"{restartMessage}"
            )
        else:
            m.setText(restartMessage)
        m.setIcon(m.Warning)
        m.setStandardButtons(m.Ok | m.Cancel)
        m.setDefaultButton(m.Cancel)
        okBtn = m.button(QtWidgets.QMessageBox.StandardButton.Ok)
        cancelBtn = m.button(QtWidgets.QMessageBox.StandardButton.Cancel)
        okBtn.setText("Restart now")
        cancelBtn.setText("Restart later")
        ret = m.exec_()
        if ret == m.Ok:
            # restart FreeCAD after a delay to give time to this dialog to close
            QtCore.QTimer.singleShot(2000, lambda: self.restartFreecad(windowState))

    def backupPrefFile(self, pathFile):
        try:
            return Utils.createBackup(pathFile)
        except FileNotFoundError as e:
            logger.error(f"Failed to create a backup of {pathFile}")
            logger.error(str(e))
            return None

    def backupPrefs(self):
        # This is the correct way to obtain the used configuration files that
        # may have been overridden with the command line user-cfg and
        # system-cfg flags
        userConfigFile = FreeCAD.ConfigGet("UserParameter")
        sysConfigFile = FreeCAD.ConfigGet("SystemParameter")

        backupFiles = []
        userConfigFileBak = self.backupPrefFile(userConfigFile)
        sysConfigFileBak = self.backupPrefFile(sysConfigFile)
        if userConfigFileBak:
            backupFiles.append(userConfigFileBak)
        if sysConfigFileBak:
            backupFiles.append(sysConfigFileBak)
        return backupFiles

    def getWindowStatePreferences(self):
        paramGroup = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
        return QByteArray(base64.b64decode(paramGroup.GetString("MainWindowState")))

    def loadPrefs(self, prefsId):
        # throws APIClientException
        result = self.api.downloadPrefs(prefsId)
        if result:
            backupFiles = self.backupPrefs()
            self.setPrefs(result)
            # Get the windows state we would like at this time to restore it as
            # late as possible.
            windowState = self.getWindowStatePreferences()
            FreeCAD.saveParameter("User parameter")
            FreeCAD.saveParameter("System parameter")
            self.askRestart(backupFiles, windowState)

        return result

    def loadPrefsOrg(self, index):
        workspaceData = self.workspacesModel.data(index)
        orgDataWorkspace = workspaceData.get("organization")
        orgId = orgDataWorkspace["_id"]
        nameOrg = orgDataWorkspace["name"]

        def tryLoadPrefs():
            orgData = self.api.getOrganization(orgId)
            prefsId = orgData.get("preferencesId")
            result = self.loadPrefs(prefsId)
            if not result:
                logger.info(f"Organization {nameOrg} has no preferences stored.")

        self.handle(tryLoadPrefs)

    def downloadOndselDefaultPrefs(self):
        def tryLoadPrefs():
            result = self.loadPrefs("000000000000000000000000")
            if not result:
                logger.error("No default preferences stored")

        self.handle(tryLoadPrefs)

    # ####
    # Directory deletion
    # ####

    def deleteEmptyDir(self, fileItem, index):
        # throws an APICLientException
        result = QtGui.QMessageBox.question(
            self.form.fileList,
            "Delete Directory",
            f"Are you sure you want to delete directory <b>{fileItem.name}</b>?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
        )
        if result == QtGui.QMessageBox.Yes:
            self.currentWorkspaceModel.deleteDirectory(index)

    def deleteDirectory(self, fileItem, index):
        wsm = self.currentWorkspaceModel

        def tryDelete():
            if wsm.isEmptyDirectory(index):
                self.deleteEmptyDir(fileItem, index)
            else:
                logger.warn(f"Directory {fileItem.name} is not empty")

        self.handle(tryDelete)

    # ####
    # File deletion
    # ####

    def confirmDelete(self, fileName, where, additionalInfo=""):
        return QtGui.QMessageBox.question(
            self.form.fileList,
            "Delete File",
            "Are you sure you want to delete file "
            f"<b>{fileName}</b> from {where}?{additionalInfo}",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
        )

    def confirmDeleteLens(self, fileName):
        additionalInfo = """<br><br>Deleting this file also deletes:
        <ul>
          <li>All file revisions</li>
          <li>Any 3D models of the file (current or past)</li>
          <li>All share links to any of the file's revisions</li>
        </ul>
        """
        return self.confirmDelete(fileName, "Lens", additionalInfo)

    def confirmDeleteLocally(self, fileName):
        return self.confirmDelete(fileName, "the local file system")

    def deleteFileConnected(self, fileItem, index):
        fileName = fileItem.name
        if fileItem.status == FileStatus.SERVER_ONLY:
            if self.confirmDeleteLens(fileName) == QtGui.QMessageBox.Yes:
                self.handle(lambda: self.currentWorkspaceModel.deleteFile(index))
        elif fileItem.status in [
            FileStatus.UNTRACKED,
            FileStatus.LOCAL_COPY_OUTDATED,
            FileStatus.SERVER_COPY_OUTDATED,
            FileStatus.SYNCED,
        ]:
            if self.confirmDeleteLocally(fileName) == QtGui.QMessageBox.Yes:
                self.currentWorkspaceModel.deleteFileLocally(index)

    def deleteFileDisconnected(self, fileItem, index):
        if self.confirmDeleteLocally(fileItem.name) == QtGui.QMessageBox.Yes:
            self.currentWorkspaceModel.deleteFile(index)

    def deleteFile(self, fileItem, index):
        if self.is_connected():
            self.deleteFileConnected(fileItem, index)
        else:
            self.deleteFileDisconnected(fileItem, index)

    def showFileContextMenuFile(self, file_item, pos, index):
        menu = QtGui.QMenu()
        openOnlineAction = menu.addAction("View in Lens")
        uploadAction = menu.addAction("Upload to Lens")
        downloadAction = menu.addAction("Download from Lens")
        menu.addSeparator()
        deleteAction = menu.addAction("Delete File")
        if self.is_connected():
            if file_item.status == FileStatus.SERVER_ONLY:
                uploadAction.setEnabled(False)
            if file_item.status == FileStatus.UNTRACKED:
                downloadAction.setEnabled(False)
            if file_item.ext not in [".fcstd", ".obj"]:
                openOnlineAction.setEnabled(False)
        else:
            uploadAction.setEnabled(False)
            downloadAction.setEnabled(False)
            openOnlineAction.setEnabled(False)

        action = menu.exec_(self.form.fileList.viewport().mapToGlobal(pos))

        if action == deleteAction:
            self.deleteFile(file_item, index)
        if action == openOnlineAction:
            self.openModelOnline(file_item.getModelId())
        elif action == downloadAction:
            self.downloadFileIndex(index)
        elif action == uploadAction:
            self.upload(index, file_item)

    # ####
    # Uploading files (initial commit or updating a version
    # ####

    def uploadFile(
        self,
        fileItem,
        fileName,
        fileId=None,
        message="Update from the Ondsel Lens addon",
    ):
        """Upload a file via the workspace model.

        Interacts with the API.
        """

        def tryUpload():
            wsm = self.currentWorkspaceModel
            if fileId:
                # updating an existing version
                wsm.upload(fileName, fileId, message)
            else:
                # initial commit
                wsm.upload(fileName)
            wsm.refreshModel()
            if self.form.versionsComboBox.isVisible():
                model = self.form.versionsComboBox.model()
                model.refreshModel(fileItem)
                self.form.versionsComboBox.setCurrentIndex(model.getCurrentIndex())
                logger.debug("versionComboBox setCurrentIndex")

        self.handle(tryUpload)

    def enterCommitMessage(self):
        dialog = EnterCommitMessageDialog()
        if dialog.exec_() == QtGui.QDialog.Accepted:
            return dialog.getCommitMessage()
        else:
            return None

    def uploadWithCommitMessage(self, fileItem, debugMessage):
        commitMessage = self.enterCommitMessage()
        if commitMessage:
            logger.debug(f"Upload a file {fileItem.name} {debugMessage}")
            self.uploadFile(
                fileItem, fileItem.name, fileItem.serverFileDict["_id"], commitMessage
            )

    def confirmUpload(self, message):
        return self.confirmFileTransfer(
            message, "Uploading will override the server version."
        )

    def upload(self, index, fileItem):
        """Upload a file.

        First perform various checks / ask confirmation.
        """
        if fileItem.is_folder:
            logger.info("Upload of folders not supported.")
        else:
            # TODO: in a shared setting refreshing is dangerous, suppose
            # another user pushes a file, then the index does not point to the
            # correct file any longer.
            # First we refresh to make sure the file status have not changed.
            # self.refreshModel()

            # Check if the file is not newer on the server first.
            if fileItem.status == FileStatus.LOCAL_COPY_OUTDATED:
                msg = "The local copy is outdated compared to the active version."
                if not self.confirmUpload(msg):
                    return
                else:
                    self.uploadWithCommitMessage(fileItem, "with local copy outdated")
            elif fileItem.status is FileStatus.UNTRACKED:
                logger.debug(f"Upload untracked file {fileItem.name}")
                # Initial commit
                self.uploadFile(fileItem, fileItem.name)
            elif fileItem.status is FileStatus.SERVER_COPY_OUTDATED:
                self.uploadWithCommitMessage(fileItem, "that is outdated on the server")
            elif fileItem.status is FileStatus.SYNCED:
                logger.info(f"File {fileItem.name} is already in sync")
            else:
                logger.error(f"Unknown file status: {fileItem.status}")

    def showFileContextMenuDir(self, fileItem, pos, index):
        menu = QtGui.QMenu()
        deleteAction = menu.addAction("Delete Directory")

        action = menu.exec_(self.form.fileList.viewport().mapToGlobal(pos))
        if action == deleteAction:
            self.deleteDirectory(fileItem, index)

    def showFileContextMenu(self, pos):
        index = self.form.fileList.indexAt(pos)
        file_item = self.currentWorkspaceModel.data(index)
        if file_item is None:
            return

        if file_item.is_folder:
            self.showFileContextMenuDir(file_item, pos, index)
        else:
            self.showFileContextMenuFile(file_item, pos, index)

    def showLinksContextMenu(self, pos):
        index = self.form.linksView.indexAt(pos)

        if index.isValid():
            menu = QtGui.QMenu()
            shareLinkAction = menu.addAction("Share link")
            editLinkAction = menu.addAction("Edit")
            deleteAction = menu.addAction("Delete")

            action = menu.exec_(self.form.linksView.viewport().mapToGlobal(pos))

            if action == shareLinkAction:
                self.shareShareLinkClicked(index)
            elif action == editLinkAction:
                self.editShareLinkClicked(index)
            elif action == deleteAction:
                self.deleteShareLinkClicked(index)
        else:
            menu = QtGui.QMenu()
            addLinkAction = menu.addAction("add link")

            action = menu.exec_(self.form.linksView.viewport().mapToGlobal(pos))

            if action == addLinkAction:
                self.addShareLink()

    def shareShareLinkClicked(self, index):
        model = self.form.linksView.model()
        shareLinkId = model.data(index, ShareLinkModel.UrlRole)

        direct_link = model.compute_direct_link(shareLinkId)
        forum_shortcode = model.compute_forum_shortcode(shareLinkId)
        iframe = model.compute_iframe(shareLinkId)

        # Create a custom dialog
        dialog = QtGui.QDialog(
            self.form, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint
        )  # Set dialog as a popup without title bar
        dialog.setWindowTitle("Share Options")
        dialog.setWindowModality(QtCore.Qt.NonModal)  # Set dialog to non-modal

        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel("Share Model")
        layout.addWidget(label)

        direct_link_button = QtGui.QPushButton("Direct link")
        direct_link_button.setToolTip(
            "Copy to the clipboard the link with which "
            "anyone can visit this model on Ondsel Lens."
        )

        forum_button = QtGui.QPushButton("Share in FreeCAD forum")
        forum_button.setToolTip(
            "Copy to the clipboard a shortcode "
            "that you can paste in FreeCAD forum posts "
            "to embed a view of your model."
        )

        embed_button = QtGui.QPushButton("Embed")
        embed_button.setToolTip(
            "Copy to the clipboard the HTML with which you can "
            "embed a view of your model in a website."
        )

        # Add buttons to the layout
        layout.addWidget(direct_link_button)
        layout.addWidget(forum_button)
        layout.addWidget(embed_button)

        def closeWithAction(contents, message):
            self.copyToClipboard(contents, message)
            dialog.close()

        # Connect button actions
        direct_link_button.clicked.connect(
            lambda: closeWithAction(direct_link, "Link to the model on Ondsel Lens")
        )
        forum_button.clicked.connect(
            lambda: closeWithAction(forum_shortcode, "Forum shortcode")
        )
        embed_button.clicked.connect(
            lambda: closeWithAction(iframe, "HTML to embed the model")
        )

        # Set the layout for the dialog
        dialog.setLayout(layout)

        # Calculate the position near the mouse cursor
        dialog.show()  # Need to show the dialog so geometry is computed
        cursor_pos = QtGui.QCursor.pos()
        screen_geometry = QApplication.desktop().availableGeometry(dialog)
        dialog_geometry = dialog.geometry()
        x_min = screen_geometry.x() + 10
        y_min = screen_geometry.y() + 10
        x_max = (
            screen_geometry.x() + screen_geometry.width() - dialog_geometry.width() - 10
        )
        y_max = (
            screen_geometry.y()
            + screen_geometry.height()
            - dialog_geometry.height()
            - 10
        )

        x = max(min(cursor_pos.x(), x_max), x_min)
        y = max(min(cursor_pos.y(), y_max), y_min)

        # Set the adjusted position
        dialog.move(x, y)

        # Show the dialog
        dialog.exec_()

    def copyToClipboard(self, text, message):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        logger.info(f"{message} copied to the clipboard.")

    def editShareLinkClicked(self, index):
        model = self.form.linksView.model()
        linkData = model.data(index, ShareLinkModel.EditLinkRole)

        dialog = SharingLinkEditDialog(linkData, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()
            self.handle(lambda: model.update_link(index, link_properties))

    def deleteShareLinkClicked(self, index):
        model = self.form.linksView.model()
        linkId = model.data(index, ShareLinkModel.UrlRole)
        result = QtGui.QMessageBox.question(
            None,
            "Delete Link",
            "Are you sure you want to delete this link?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
        )
        if result == QtGui.QMessageBox.Yes:
            self.handle(lambda: model.delete_link(linkId))

    def addShareLink(self):
        dialog = SharingLinkEditDialog(None, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()

            self.handle(
                lambda: self.form.linksView.model().add_new_link(link_properties)
            )

    def openUrl(self, url):
        # doesn't work on platforms without `gio-launch-desktop` while Qt
        # tries to use this.
        # ret = QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        logger.debug(f"Attempting to open {url}")
        if not webbrowser.open(url):
            logger.warn(f"Failed to open {url} in the browser")

    def openModelOnline(self, modelId=None):
        url = ondselUrl

        if not modelId:
            comboBox = self.form.versionsComboBox
            versionModel = comboBox.model()
            modelId = versionModel.model_id

        logger.debug(f"modelId: {modelId}")
        if modelId is not None:
            url = f"{lensUrl}model/{modelId}"
            logger.debug(f"Opening {url}")
        self.openUrl(url)

    def makeActive(self):
        comboBox = self.form.versionsComboBox
        versionModel = comboBox.model()
        fileItem = versionModel.fileItem
        fileId = fileItem.serverFileDict["_id"]
        versionId = versionModel.getCurrentVersionId()

        def trySetVersion():
            self.api.setVersionActive(fileId, versionId)
            # refresh the models
            wsm = self.currentWorkspaceModel
            wsm.refreshModel()
            newFileItem = wsm.getFileItemFileId(fileItem.serverFileDict["_id"])
            versionModel.refreshModel(newFileItem)
            comboBox.setCurrentIndex(versionModel.getCurrentIndex())
            self.form.makeActiveBtn.setVisible(versionModel.canBeMadeActive())

        self.handle(trySetVersion)

    def ondselAccount(self):
        url = f"{lensUrl}login"
        self.openUrl(url)

    def showOndselSignUpPage(self):
        url = f"{lensUrl}signup"
        self.openurl(url)

    def timerTick(self):
        def tryRefresh():
            if self.current_workspace is not None:
                self.currentWorkspaceModel.refreshModel()
            else:
                self.workspacesModel.refreshModel()

        self.handle(tryRefresh)

    # ####
    # Adding files and directories
    # ####

    def addCurrentFile(self):
        # Save current file on the server.
        doc = FreeCAD.ActiveDocument
        gui_doc = Gui.ActiveDocument

        if doc is None:
            QMessageBox.information(
                self,
                "No FreeCAD File Opened",
                "You don't have any FreeCAD file opened now.",
            )
            return
        wsm = self.currentWorkspaceModel
        # Get the default name of the file from the document
        default_name = doc.Label + ".FCStd"
        default_path = wsm.getFullPath()
        default_file_path = Utils.joinPath(default_path, default_name)

        doc.FileName = default_file_path
        gui_doc.ActiveView.sendMessage("SaveAs")

        fileName = os.path.basename(doc.FileName)

        # Open a dialog box for the user to select a file location and name
        # file_name, _ = QtGui.QFileDialog.getSaveFileName(
        #     self, "Save File", default_file_path, "FreeCAD file (*.fcstd)"
        # )

        # if file_name:
        #     # Make sure the file has the correct extension
        #     if not file_name.lower().endswith(".fcstd"):
        #         file_name += ".FCStd"
        #     # Save the file
        #     FreeCAD.Console.PrintMessage(f"Saving document to file: {file_name}\n")
        #     doc.saveAs(file_name)

        def tryUpload():
            if self.is_connected():
                wsm.upload(fileName)
            wsm.refreshModel()

        self.handle(tryUpload)
        self.switchView()

    def addSelectedFiles(self):
        # open file browser dialog to select files to copy
        selectedFiles, _ = QtGui.QFileDialog.getOpenFileNames(
            None,
            "Select Files",
            os.path.expanduser("~"),
            "All Files (*);;Text Files (*.txt)",
        )

        wsm = self.currentWorkspaceModel

        # copy selected files to destination folder
        for fileUrl in selectedFiles:
            fileName = os.path.basename(fileUrl)
            destFileUrl = Utils.joinPath(wsm.getFullPath(), fileName)

            try:
                shutil.copy(fileUrl, destFileUrl)
            except (shutil.SameFileError, OSError):
                QtGui.QMessageBox.warning(
                    None, "Error", "Failed to copy file " + fileName
                )

        # after copying try the upload
        def tryUpload():
            if self.is_connected():
                for fileUrl in selectedFiles:
                    fileName = os.path.basename(fileUrl)
                    destFileUrl = Utils.joinPath(wsm.getFullPath(), fileName)
                    if os.path.isfile(destFileUrl):
                        wsm.upload(fileName)
                    else:
                        logger.warning(f"Failed to upload {fileName}")
            wsm.refreshModel()

        self.handle(tryUpload)
        self.switchView()

    def addDir(self):
        existingFileNames = self.currentWorkspaceModel.getFileNames()
        dialog = CreateDirDialog(existingFileNames)

        def tryCreateDir():
            if dialog.exec_() == QtGui.QDialog.Accepted:
                dir = dialog.getDir()
                self.currentWorkspaceModel.createDir(dir)
            self.currentWorkspaceModel.refreshModel()

        self.handle(tryCreateDir)
        self.switchView()

    # def newWorkspaceBtnClicked(self):
    #     if self.api is None and self.access_token is None:
    #         logger.debug("You need to login first")
    #         self.login_btn_clicked()
    #         return
    #     if self.api is None and self.access_token is not None:
    #         self.api = APIClient(
    #             "", "", baseUrl, lensUrl, self.access_token, self.user
    #         )

    #     dialog = NewWorkspaceDialog()
    #     # Show the dialog and wait for the user to close it
    #     if dialog.exec_() == QtGui.QDialog.Accepted:
    #         workspaceName = dialog.nameEdit.text()
    #         workspaceDesc = dialog.descEdit.toPlainText()

    #         personal_organisation = None
    #         for organization in self.user["organizations"]:
    #             if organization.get("name") == "Personal":
    #                 personal_organisation = organization.get("_id")
    #                 break

    #         if personal_organisation is None:
    #             return

    #         self.api.createWorkspace(
    #             workspaceName, workspaceDesc, personal_organisation
    #         )

    #         # workspaceType = "Ondsel"
    #         # workspaceId = result["_id"]
    #         # workspaceUrl = cachePath + workspaceId #workspace id.
    #         # workspaceRootDir = result["rootDirectory"]

    #         self.workspacesModel.refreshModel()

    #         # # Determine workspace type and get corresponding values
    #         # if dialog.localRadio.isChecked():
    #         #     workspaceType = "Local"
    #         #     workspaceUrl = dialog.localFolderLabel.text()
    #         # elif dialog.ondselRadio.isChecked():
    #         #     workspaceType = "Ondsel"
    #         #     workspaceUrl = cachePath + dialog.nameEdit.text()
    #         # else:
    #         #     workspaceType = "External"
    #         #     workspaceUrl = dialog.externalServerEdit.text()
    #         # Update workspaceListWidget with new workspace

    def get_server_package_file(self):
        response = requests.get(remote_package_url, timeout=5)
        if response.status_code == 200:
            return response.text
        return None

    def get_local_package_file(self):
        try:
            with open(Utils.local_package_path, "r") as file_:
                return file_.read()
        except FileNotFoundError:
            pass
        return None

    def get_version_from_package_file(self, packageFileStr):
        if packageFileStr is None:
            return None
        lines = packageFileStr.split("\n")
        for line in lines:
            if "<version>" in line:
                version = line.strip().lstrip("<version>").rstrip("</version>")
                return version

    def get_latest_version_ondsel_es(self):
        # raises a ReqestException
        response = requests.get(
            "https://api.github.com/repos/Ondsel-Development/FreeCAD/releases/latest"
        )

        if response.status_code == requests.codes.ok:
            json = response.json()
            return json.get("tag_name")

        return None

    def get_freecad_version_number(self):
        version = FreeCAD.Version()
        return f"{version[0]}.{version[1]}.{version[2]}"

    def get_current_version_number_ondsel_es(self):
        if self.get_source() == "ondseles":
            return self.get_freecad_version_number()

        return None

    def get_current_version_freecad(self):
        version = FreeCAD.Version()

        return ", ".join([self.get_freecad_version_number()] + version[3:])

    def get_source(self):
        vendor = FreeCAD.ConfigGet("ExeVendor")
        if vendor == "Ondsel":
            return "ondseles"
        elif vendor == "FreeCAD":
            return "freecad"
        else:
            return "unknown"

    def get_version(self):
        return (
            self.get_current_version_freecad() + ", addon: " + Utils.get_addon_version()
        )

    def openDownloadPage(self):
        url = f"{self.api.get_base_url()}download-and-explore"
        self.openUrl(url)

    def toVersionNumber(self, version):
        return [int(n) for n in version.split(".")]

    def version_greater_than(self, latestVersion, currentVersion):
        latestV = self.toVersionNumber(latestVersion)
        currentV = self.toVersionNumber(currentVersion)
        if len(latestV) != len(currentV):
            return False  # don't report

        for i in range(len(latestV)):
            if latestV[i] > currentV[i]:
                return True
            elif latestV[i] < currentV[i]:
                return False
            else:
                # these version numbers are the same, so look at the next
                # version number
                pass

        # All are the same
        return False

    def check_for_update_ondsel_es(self):
        # raises a RequestException
        currentVersion = self.get_current_version_number_ondsel_es()
        if currentVersion:
            latestVersion = self.get_latest_version_ondsel_es()
            if latestVersion and self.version_greater_than(
                latestVersion, currentVersion
            ):
                self.set_frame_update("Ondsel ES", latestVersion, self.openDownloadPage)

    def set_frame_update(self, name, version, function):
        self.form.labelUpdateAvailable.setText(f"{name} v{version} available!")
        self.form.updateBtn.clicked.disconnect()
        self.form.updateBtn.clicked.connect(function)
        self.form.frameUpdate.show()

    def check_for_update(self):
        # raises a RequestException
        local_version = self.get_version_from_package_file(
            self.get_local_package_file()
        )
        remote_version = self.get_version_from_package_file(
            self.get_server_package_file()
        )

        if local_version and remote_version and local_version != remote_version:
            self.set_frame_update("Ondsel Lens", remote_version, self.openAddonManager)
        else:
            self.check_for_update_ondsel_es()

    # ####
    # Bookmarks / tabs
    # ####

    def onTabChanged(self, index):
        if index == IDX_TAB_BOOKMARKS:

            def tryRefresh():
                bookmarkModel = getBookmarkModel(self.api)
                viewBookmarks = self.form.viewBookmarks
                viewBookmarks.setModel(bookmarkModel)
                viewBookmarks.expandAll()

            self.handle(tryRefresh)

    def downloadBookmarkFile(self, idSharedModel):
        # throws an APIClientException
        path = Utils.joinPath(PATH_BOOKMARKS, idSharedModel)
        sharedModel = self.api.getSharedModel(idSharedModel)
        model = sharedModel["model"]
        if sharedModel["canDownloadDefaultModel"]:
            uniqueFileName = model["uniqueFileName"]
            fileModel = model["file"]
            fileName = fileModel["custFileName"]
            pathFile = Utils.joinPath(path, fileName)
            self.api.downloadFileFromServer(uniqueFileName, pathFile)
            return pathFile
        else:
            objUrl = model["objUrl"]
            fileName = Utils.getFileNameFromURL(objUrl)
            pathFile = Utils.joinPath(path, fileName)
            self.api.downloadObjectFileFromServer(objUrl, pathFile)
            return pathFile

    def openBookmark(self, idSharedModel):
        # throws an APIClientException
        pathFile = self.downloadBookmarkFile(idSharedModel)
        self.tryOpenPathFile(pathFile)

    def bookmarkDoubleClicked(self, index):
        viewBookmarks = self.form.viewBookmarks
        bookmarkModel = viewBookmarks.model()
        typeItem = bookmarkModel.data(index, ROLE_TYPE)
        if typeItem == TYPE_BOOKMARK:
            idShareModel = bookmarkModel.data(index, ROLE_SHARE_MODEL_ID)
            self.handle(lambda: self.openBookmark(idShareModel))

    def openShareLinkOnline(self, idShareModel):
        url = f"{self.api.get_base_url()}share/{idShareModel}"
        self.openUrl(url)

    def showBookmarkContextMenu(self, pos):
        viewBookmarks = self.form.viewBookmarks
        index = viewBookmarks.indexAt(pos)
        if index.isValid():
            bookmarkModel = viewBookmarks.model()
            typeItem = bookmarkModel.data(index, ROLE_TYPE)
            if typeItem == TYPE_BOOKMARK:
                menu = QtGui.QMenu()
                openAction = menu.addAction("Open bookmark")
                viewAction = menu.addAction("View the bookmark in Lens")

                action = menu.exec_(viewBookmarks.viewport().mapToGlobal(pos))

                idShareModel = bookmarkModel.data(index, ROLE_SHARE_MODEL_ID)
                if action == openAction:
                    self.handle(lambda: self.openBookmark(idShareModel))
                elif action == viewAction:
                    self.openShareLinkOnline(idShareModel)


# class NewWorkspaceDialog(QtGui.QDialog):
#     def __init__(self, parent=None):
#         super(NewWorkspaceDialog, self).__init__(parent)
#         self.setWindowTitle("Add Workspace")
#         self.setModal(True)

#         layout = QtGui.QVBoxLayout()

#         # Radio buttons for selecting workspace type
#         # self.localRadio = QtGui.QRadioButton("Local")
#         # self.ondselRadio = QtGui.QRadioButton("Ondsel Server")
#         # self.ondselRadio.setToolTip(
#         #     "Ondsel currently supports only one workspace "
#         #     "that is added automatically on login."
#         # )
#         # self.ondselRadio.setEnabled(False)
#         # self.externalRadio = QtGui.QRadioButton("External Server")
#         # self.externalRadio.setToolTip(
#         #     "Currently external servers support is not implemented."
#         # )
#         # self.externalRadio.setEnabled(False)

#         # button_group = QtGui.QButtonGroup()
#         # button_group.addButton(self.localRadio)
#         # button_group.addButton(self.ondselRadio)
#         # button_group.addButton(self.externalRadio)

#         # group_box = QtGui.QGroupBox("type")
#         # group_box_layout = QtGui.QHBoxLayout()
#         # group_box_layout.addWidget(self.localRadio)
#         # group_box_layout.addWidget(self.ondselRadio)
#         # group_box_layout.addWidget(self.externalRadio)
#         # group_box.setLayout(group_box_layout)

#         # Workspace Name
#         self.nameLabel = QtGui.QLabel("Name")
#         self.nameEdit = QtGui.QLineEdit()
#         nameHlayout = QtGui.QHBoxLayout()
#         nameHlayout.addWidget(self.nameLabel)
#         nameHlayout.addWidget(self.nameEdit)

#         # Workspace description
#         self.descLabel = QtGui.QLabel("Description")
#         self.descEdit = QtGui.QTextEdit()

#         # # Widgets for local workspace type
#         # self.localFolderLabel = QtGui.QLineEdit("")
#         # self.localFolderEdit = QtGui.QPushButton("Select folder")
#         # self.localFolderEdit.clicked.connect(self.show_folder_picker)
#         # h_layout = QtGui.QHBoxLayout()
#         # h_layout.addWidget(self.localFolderLabel)
#         # h_layout.addWidget(self.localFolderEdit)

#         # # Widgets for external server workspace type
#         # self.externalServerLabel = QtGui.QLabel("Server URL")
#         # self.externalServerEdit = QtGui.QLineEdit()

#         # Add widgets to layout
#         # layout.addWidget(group_box)
#         layout.addLayout(nameHlayout)
#         layout.addWidget(self.descLabel)
#         layout.addWidget(self.descEdit)
#         # layout.addLayout(h_layout)
#         # layout.addWidget(self.externalServerLabel)
#         # layout.addWidget(self.externalServerEdit)

#         # Connect radio buttons to updateDialog function
#         # self.localRadio.toggled.connect(self.updateDialog)
#         # self.ondselRadio.toggled.connect(self.updateDialog)
#         # self.externalRadio.toggled.connect(self.updateDialog)
#         # self.localRadio.setChecked(True)

#         # Add OK and Cancel buttons
#         buttonBox = QtGui.QDialogButtonBox(
#             QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
#         )
#         buttonBox.accepted.connect(self.accept)
#         buttonBox.rejected.connect(self.reject)

#         # Add layout and buttons to dialog
#         self.setLayout(layout)
#         layout.addWidget(buttonBox)

#     # Function to update the dialog when the workspace type is changed
#     def updateDialog(self):
#         pass
#         # if self.ondselRadio.isChecked():
#         #     self.nameLabel.setText("ondsel.com/")
#         # else:
#         #     self.nameLabel.setText("Name")
#         # self.localFolderLabel.setVisible(self.localRadio.isChecked())
#         # self.localFolderEdit.setVisible(self.localRadio.isChecked())

#         # self.externalServerLabel.setVisible(self.externalRadio.isChecked())
#         # self.externalServerEdit.setVisible(self.externalRadio.isChecked())

#     # def show_folder_picker(self):
#     #     options = QtGui.QFileDialog.Options()
#     #     options |= QtGui.QFileDialog.ShowDirsOnly
#     #     folder_url = QtGui.QFileDialog.getExistingDirectory(
#     #         self, "Select Folder", options=options
#     #     )
#     #     if folder_url:
#     #         self.localFolderLabel.setText(folder_url)

#     # def okClicked(self):
#     #    pass
#     # if self.localRadio.isChecked():
#     #    if os.path.isdir(self.localFolderLabel.text()):
#     #        self.accept()
#     #    else:
#     #        result = QtGui.QMessageBox.question(
#     #            self,
#     #            "Wrong URL",
#     #            "The URL you entered is not correct.",
#     #            QtGui.QMessageBox.Ok,
#     #        )

PROTECTION_COMBO_BOX_LISTED = 0
PROTECTION_COMBO_BOX_UNLISTED = 1
PROTECTION_COMBO_BOX_PIN = 2
VERSION_FOLLOWING_COMBO_BOX_LOCKED = 0
VERSION_FOLLOWING_COMBO_BOX_ACTIVE = 1


class SharingLinkEditDialog(QtGui.QDialog):
    def __init__(self, linkProperties=None, parent=None):
        super(SharingLinkEditDialog, self).__init__(parent)

        # Load the UI from the .ui file
        self.dialog = Gui.PySideUic.loadUi(Utils.mod_path + "/SharingLinkEditDialog.ui")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.dialog)
        self.setLayout(layout)

        self.dialog.okBtn.clicked.connect(self.accept)
        self.dialog.cancelBtn.clicked.connect(self.reject)
        self.dialog.protectionComboBox.currentIndexChanged.connect(
            self.protection_changed
        )
        self.dialog.versionFollowingComboBox.currentIndexChanged.connect(
            self.version_following_changed
        )

        if linkProperties is None:
            self.linkProperties = {
                "isActive": True,
                "isSystemGenerated": False,
                "title": "",
                "description": "",
                "protection": "Listed",
                "pin": "",
                "versionFollowing": "Locked",
                "canViewModelAttributes": True,
                "canUpdateModel": True,
                "canExportFCStd": True,
                "canExportSTEP": True,
                "canExportSTL": True,
                "canExportOBJ": True,
                "isActive": True,
                "canViewModel": True,
                "canDownloadDefaultModel": True,
            }
            self.creationAction = True  # we are creating a new share link
        else:
            self.linkProperties = linkProperties
            self.creationAction = False  # we are editing an existing share link

        if self.creationAction:
            self.setWindowTitle("Create ShareLink")
            self.dialog.enabledCheckBox.setVisible(False)
        else:
            self.setWindowTitle("Edit ShareLink")
            # once created, you can NEVER change versionFollowing or protection
            self.dialog.versionFollowingComboBox.setEnabled(False)
            self.dialog.protectionComboBox.setEnabled(False)
        if self.linkProperties["isSystemGenerated"]:
            # cannot enable/disable a sys generated link
            self.dialog.enabledCheckBox.setEnabled(False)
        self.setLinkProperties()
        self.protection_changed()  # do this to set initial PIN edit visibility
        self.version_following_changed()

    def protection_changed(self):
        protectionIndex = self.dialog.protectionComboBox.currentIndex()
        if protectionIndex == PROTECTION_COMBO_BOX_PIN:
            if self.dialog.pinLineEdit.text() == "":
                random_str = ""
                for i in range(6):
                    new_digit = math.floor(random.random() * 10)
                    random_str += str(new_digit)
                self.dialog.pinLineEdit.setText(random_str)
            self.dialog.pinLabel.setVisible(True)
            self.dialog.pinLineEdit.setVisible(True)
        else:
            self.dialog.pinLabel.setVisible(False)
            self.dialog.pinLineEdit.setVisible(False)

    def version_following_changed(self):
        vfIndex = self.dialog.versionFollowingComboBox.currentIndex()
        if vfIndex == VERSION_FOLLOWING_COMBO_BOX_ACTIVE:
            self.dialog.canExportFCStdCheckBox.setChecked(False)
            self.dialog.canExportFCStdCheckBox.setEnabled(False)
            self.dialog.canExportSTEPCheckBox.setChecked(False)
            self.dialog.canExportSTEPCheckBox.setEnabled(False)
            self.dialog.canExportSTLCheckBox.setChecked(False)
            self.dialog.canExportSTLCheckBox.setEnabled(False)
            self.dialog.canExportOBJCheckBox.setChecked(False)
            self.dialog.canExportOBJCheckBox.setEnabled(False)
            self.dialog.canUpdateModelAttributesCheckBox.setChecked(False)
            self.dialog.canUpdateModelAttributesCheckBox.setEnabled(False)
        else:
            self.dialog.canExportFCStdCheckBox.setEnabled(True)
            self.dialog.canExportSTEPCheckBox.setEnabled(True)
            self.dialog.canExportSTLCheckBox.setEnabled(True)
            self.dialog.canExportOBJCheckBox.setEnabled(True)
            self.dialog.canUpdateModelAttributesCheckBox.setEnabled(True)

    def setLinkProperties(self):
        self.dialog.linkTitle.setText(self.linkProperties["title"])
        self.dialog.linkName.setText(self.linkProperties["description"])
        if self.linkProperties["protection"] == "Listed":
            self.dialog.protectionComboBox.setCurrentIndex(PROTECTION_COMBO_BOX_LISTED)
        elif self.linkProperties["protection"] == "Unlisted":
            self.dialog.protectionComboBox.setCurrentIndex(
                PROTECTION_COMBO_BOX_UNLISTED
            )
        elif self.linkProperties["protection"] == "Pin":
            self.dialog.protectionComboBox.setCurrentIndex(PROTECTION_COMBO_BOX_PIN)
        self.dialog.pinLineEdit.setText(self.linkProperties["pin"])
        if self.linkProperties["versionFollowing"] == "Locked":
            self.dialog.versionFollowingComboBox.setCurrentIndex(
                VERSION_FOLLOWING_COMBO_BOX_LOCKED
            )
        elif self.linkProperties["versionFollowing"] == "Active":
            self.dialog.versionFollowingComboBox.setCurrentIndex(
                VERSION_FOLLOWING_COMBO_BOX_ACTIVE
            )
        self.dialog.canViewModelCheckBox.setChecked(self.linkProperties["canViewModel"])
        self.dialog.canViewModelAttributesCheckBox.setChecked(
            self.linkProperties["canViewModelAttributes"]
        )
        self.dialog.canUpdateModelAttributesCheckBox.setChecked(
            self.linkProperties["canUpdateModel"]
        )
        self.dialog.canDownloadOriginalCheckBox.setChecked(
            self.linkProperties["canDownloadDefaultModel"]
        )
        self.dialog.canExportFCStdCheckBox.setChecked(
            self.linkProperties["canExportFCStd"]
        )
        self.dialog.canExportSTEPCheckBox.setChecked(
            self.linkProperties["canExportSTEP"]
        )
        self.dialog.canExportSTLCheckBox.setChecked(self.linkProperties["canExportSTL"])
        self.dialog.canExportOBJCheckBox.setChecked(self.linkProperties["canExportOBJ"])
        self.dialog.enabledCheckBox.setChecked(self.linkProperties["isActive"])

    def getLinkProperties(self):
        self.linkProperties["title"] = self.dialog.linkTitle.text()
        self.linkProperties["description"] = self.dialog.linkName.text()
        protectionIndex = self.dialog.protectionComboBox.currentIndex()
        if protectionIndex == PROTECTION_COMBO_BOX_UNLISTED:
            self.linkProperties["protection"] = "Unlisted"
            self.linkProperties["pin"] = ""
        elif protectionIndex == PROTECTION_COMBO_BOX_PIN:
            self.linkProperties["protection"] = "Pin"
            self.linkProperties["pin"] = self.dialog.pinLineEdit.text()
        else:
            self.linkProperties["protection"] = "Listed"  # the default
            self.linkProperties["pin"] = ""
        versionFollowingIndex = self.dialog.versionFollowingComboBox.currentIndex()
        if versionFollowingIndex == VERSION_FOLLOWING_COMBO_BOX_ACTIVE:
            self.linkProperties["versionFollowing"] = "Active"
        else:
            self.linkProperties["versionFollowing"] = "Locked"  # the default
        self.linkProperties["canViewModel"] = (
            self.dialog.canViewModelCheckBox.isChecked()
        )
        self.linkProperties["canViewModelAttributes"] = (
            self.dialog.canViewModelAttributesCheckBox.isChecked()
        )
        self.linkProperties["canUpdateModel"] = (
            self.dialog.canUpdateModelAttributesCheckBox.isChecked()
        )
        self.linkProperties["canExportFCStd"] = (
            self.dialog.canExportFCStdCheckBox.isChecked()
        )
        self.linkProperties["canExportSTEP"] = (
            self.dialog.canExportSTEPCheckBox.isChecked()
        )
        self.linkProperties["canExportSTL"] = (
            self.dialog.canExportSTLCheckBox.isChecked()
        )
        self.linkProperties["canExportOBJ"] = (
            self.dialog.canExportOBJCheckBox.isChecked()
        )
        self.linkProperties["canDownloadDefaultModel"] = (
            self.dialog.canDownloadOriginalCheckBox.isChecked()
        )
        self.linkProperties["isActive"] = self.dialog.enabledCheckBox.isChecked()

        return self.linkProperties


class EnterCommitMessageDialog(QtGui.QDialog):
    MAX_LENGTH_COMMIT_MESSAGE = 50

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commit Message")

        self.label = QtGui.QLabel("Please provide a commit message:")
        self.commit_message_input = QtGui.QLineEdit()
        self.commit_message_input.setMaxLength(
            EnterCommitMessageDialog.MAX_LENGTH_COMMIT_MESSAGE
        )

        self.upload_button = QtGui.QPushButton("Upload")
        self.upload_button.clicked.connect(self.accept)

        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.upload_button.setEnabled(False)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.commit_message_input)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.upload_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Connect textChanged signals to enable/disable the create button
        self.commit_message_input.textChanged.connect(self.check_commit_message)

    def check_commit_message(self):
        commit_message = self.commit_message_input.text()
        enabled = len(commit_message) > 0
        self.upload_button.setEnabled(enabled)

    def getCommitMessage(self):
        return self.commit_message_input.text()


class CreateDirDialog(QtGui.QDialog):
    def __init__(self, filenames):
        super().__init__()
        self.setWindowTitle("Create Directory")

        self.filenames = filenames
        self.label = QtGui.QLabel("Directory name:")
        self.directory_input = QtGui.QLineEdit()

        self.create_button = QtGui.QPushButton("Create")
        self.create_button.clicked.connect(self.accept)

        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.create_button.setEnabled(False)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.directory_input)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Connect textChanged signals to enable/disable the create button
        self.directory_input.textChanged.connect(self.check_dir)

    def check_dir(self):
        dir = self.directory_input.text()
        enabled = not (dir in self.filenames or dir == "")
        self.create_button.setEnabled(enabled)

    def getDir(self):
        return self.directory_input.text()


class LoginDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        self.email_label = QtGui.QLabel("Email:")
        self.email_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.email_input = QtGui.QLineEdit()
        self.email_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.password_label = QtGui.QLabel("Password:")
        self.password_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.password_input = QtGui.QLineEdit()
        self.password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_input.setEchoMode(QtGui.QLineEdit.Password)

        self.login_button = QtGui.QPushButton("Login")
        self.login_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.login_button.clicked.connect(self.login)
        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cancel_button.clicked.connect(self.reject)

        self.login_button.setEnabled(False)

        formLayout = QtGui.QFormLayout()
        formLayout.setSpacing(5)
        formLayout.addRow(self.email_label, self.email_input)
        formLayout.addRow(self.password_label, self.password_input)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.login_button)
        buttonLayout.addWidget(self.cancel_button)

        layout.addLayout(formLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        self.adjustSize()

        # Connect textChanged signals to enable/disable login button
        self.email_input.textChanged.connect(self.check_credentials)
        self.password_input.textChanged.connect(self.check_credentials)

    def check_credentials(self):
        email = self.email_input.text()
        password = self.password_input.text()
        valid_credentials = self.validate_credentials(email, password)
        self.login_button.setEnabled(valid_credentials)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        # Perform login validation and authentication here
        if self.validate_credentials(email, password):
            self.accept()
        else:
            self.show_error_message("Invalid credentials")

    def validate_credentials(self, email, password):
        # Check if email is a valid email address using a simple regular expression
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        # Check if a password has been entered
        if not password:
            return False
        # Add additional validation logic here if needed
        # Example: Check against a user database or external authentication service

        return True  # Return True if credentials are valid, False otherwise

    def show_error_message(self, message):
        # Add code to display an error message dialog to the user
        # You can use QMessageBox or your own custom dialog implementation
        pass

    def get_credentials(self):
        email = self.email_input.text()
        password = self.password_input.text()
        return email, password


wsv = None
