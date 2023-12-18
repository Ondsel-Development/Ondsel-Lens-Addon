# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import Utils

from PySide import QtCore, QtGui
import os
from datetime import datetime, timedelta
import json
import shutil
import tempfile
import re
import requests

import jwt
from jwt.exceptions import ExpiredSignatureError
import FreeCAD
import FreeCADGui as Gui

from DataModels import WorkspaceListModel
from VersionModel import LocalVersionModel, OndselVersionModel
from LinkModel import ShareLinkModel
from APIClient import APIClient, CustomAuthenticationError
from WorkSpace import WorkSpaceModel, LocalWorkspaceModel, ServerWorkspaceModel

from PySide.QtGui import (
    QStyledItemDelegate,
    QCheckBox,
    QStyle,
    QMessageBox,
    QApplication,
    QIcon,
    QAction,
    QActionGroup,
    QMenu,
    QPixmap,
)

mw = Gui.getMainWindow()
p = FreeCAD.ParamGet("User parameter:BaseApp/Ondsel")
modPath = os.path.dirname(__file__).replace("\\", "/")
iconsPath = f"{modPath}/Resources/icons/"

# Test server
# baseUrl = "https://ec2-54-234-132-150.compute-1.amazonaws.com"
# Prod server
baseUrl = "https://lens-api.ondsel.com/"
lensUrl = "https://lens.ondsel.com/"
ondselUrl = "https://www.ondsel.com/"

remote_changelog_url = (
    "https://github.com/Ondsel-Development/Ondsel-Lens/blob/master/changeLog.md"
)

remote_package_url = "https://raw.githubusercontent.com/Ondsel-Development/Ondsel-Lens/master/package.xml"
local_package_path = f"{modPath}/package.xml"

try:
    import config

    baseUrl = config.base_url
    lensUrl = config.lens_url
except ImportError:
    pass


# Simple delegate drawing an icon and text
class FileListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the data for the current index
        if not index.isValid():
            return

        fileName, status, isFolder = index.data(
            WorkSpaceModel.NameStatusAndIsFolderRole
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
        textToDisplay = fileName
        if status != "":
            textToDisplay += " (" + status + ")"

        fontMetrics = painter.fontMetrics()
        elidedText = fontMetrics.elidedText(
            textToDisplay, QtGui.Qt.ElideRight, option.rect.width()
        )
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, elidedText)


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


class WorkspaceListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the data for the current index
        workspaceData = index.data(QtCore.Qt.DisplayRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        # Set up font for the name (bold)
        name_font = painter.font()
        name_font.setBold(True)

        # Set up font for the type (normal)
        type_font = painter.font()
        type_font.setBold(False)

        # Draw the name
        name_rect = QtCore.QRect(
            option.rect.left() + 20,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height() // 3,
        )
        painter.setFont(name_font)
        painter.drawText(
            name_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            workspaceData["name"],
        )

        # Calculate the width of the name text
        name_width = painter.fontMetrics().boundingRect(workspaceData["name"]).width()

        # Draw the organization in parentheses TODO : name and not the id.

        type_text = f"({workspaceData['organizationName']})"
        type_rect = QtCore.QRect(
            option.rect.left() + 20 + name_width + 5,
            option.rect.top(),
            option.rect.width() - 20,
            option.rect.height() // 3,
        )
        painter.setFont(type_font)
        painter.drawText(
            type_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, type_text
        )

        # Adjust the height of the item
        item_height = option.rect.height() // 3
        name_rect.setHeight(item_height)
        type_rect.setHeight(item_height)

        # Draw the description
        desc_rect = QtCore.QRect(
            option.rect.left() + 20,
            type_rect.bottom(),
            option.rect.width() - 20,
            item_height,
        )
        painter.drawText(
            desc_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            workspaceData["description"],
        )

        # Draw the button
        # button_rect = QtCore.QRect(
        #     option.rect.right() - 80,  # Adjust position as needed
        #     option.rect.top() + 10,    # Adjust position as needed
        #     70, 30                      # Width and height of the button
        # )
        # painter.save()
        # painter.setPen(QtCore.Qt.NoPen)
        # painter.setBrush(QtCore.Qt.lightGray)  # Button color
        # painter.drawRoundedRect(button_rect, 5, 5)
        # painter.restore()

        # # Draw button text
        # painter.setFont(type_font)
        # painter.drawText(
        #     button_rect,
        #     QtCore.Qt.AlignCenter,
        #     "Enter"
        # )

    def sizeHint(self, option, index):
        return QtCore.QSize(100, 60)  # Adjust the desired width and height

    # def editorEvent(self, event, model, option, index):
    #     # Check if the event is a mouse button release
    #     if event.type() == QtCore.QEvent.MouseButtonRelease:
    #         # Define the button rect same as in the paint method
    #         button_rect = QtCore.QRect(
    #             option.rect.right() - 80,
    #             option.rect.top() + 10,
    #             70, 30
    #         )
    #         # Check if the click was within the button rect
    #         if button_rect.contains(event.pos()):
    #             # Handle button click here
    #             print("Button clicked for item:", index.row())
    #             return True  # Event was handled
    #     return super(WorkspaceListDelegate, self).editorEvent(event, model, option, index)


class WorkspaceView(QtGui.QDockWidget):
    currentWorkspace = None
    username = "none"
    access_token = None
    apiClient = None
    user = None

    def __init__(self):
        super(WorkspaceView, self).__init__(mw)
        self.setObjectName("workspaceView")
        self.form = Gui.PySideUic.loadUi(f"{modPath}/WorkspaceView.ui")
        self.setWidget(self.form)
        self.setWindowTitle("Ondsel Lens")

        self.createOndselButtonMenus()

        self.ondselIcon = QIcon(iconsPath + "OndselWorkbench.svg")
        self.ondselIconOff = QIcon(iconsPath + "OndselWorkbench-off.svg")
        self.form.userBtn.setIconSize(QtCore.QSize(32, 32))
        self.form.userBtn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.form.userBtn.clicked.connect(self.form.userBtn.showMenu)

        self.form.buttonBack.clicked.connect(self.backClicked)

        self.workspacesModel = WorkspaceListModel(WorkspaceView=self)
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
        addFileAction2.triggered.connect(self.addFileBtnClicked)
        addFileMenu.addAction(addFileAction2)
        self.form.addFileBtn.setMenu(addFileMenu)

        self.form.viewOnlineBtn.clicked.connect(self.openModelOnline)

        self.form.fileDetails.setVisible(False)

        explainText = """

<h1 style="text-align:center; font-weight:bold;">Welcome</h1>

<p>You're not currently logged in to the Ondsel service. Use the button above to login in or create an account. When you log in, this space will show your workspaces.</p>

<p>You can enter the workspaces by double-clicking them.</p>

<p>Each workspace is a collection of files. Think of it like a project.</p>

        """

        self.form.txtExplain.setHtml(explainText)
        self.form.txtExplain.setReadOnly(True)
        self.form.txtExplain.hide()

        # Check if user is already logged in.
        loginDataStr = p.GetString("loginData", "")
        if loginDataStr != "":
            loginData = json.loads(loginDataStr)
            self.access_token = loginData["accessToken"]
            # self.access_token = self.generate_expired_token()

            if self.isTokenExpired(self.access_token):
                user = None
                self.logout()
            else:
                self.user = loginData["user"]
                self.setUIForLogin(True, self.user)

                if self.apiClient is None:
                    self.apiClient = APIClient(
                        "", "", baseUrl, lensUrl, self.access_token, self.user
                    )

                # Set a timer to logout when token expires.
                self.setTokenExpirationTimer(self.access_token)
        else:
            user = None
            self.setUIForLogin(False)
        self.switchView()

        self.workspacesModel.refreshModel()

        # Set a timer to check regularly the server
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerTick)
        self.timer.setInterval(60000)
        self.timer.start()

        self.check_for_update()

        # linksView.setModel(self.linksModel)

    # def generate_expired_token(self):
    #     # generate an expired token for testing
    #     expiration_time = datetime.now() - timedelta(minutes=5)  # Set expiration time to 5 minutes ago
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

        a = QAction("Ondsel Account", userActions)
        a.triggered.connect(self.ondselAccount)
        self.userMenu.addAction(a)

        self.synchronizeAction = QAction("Synchronize", userActions)
        self.synchronizeAction.setVisible(False)
        self.userMenu.addAction(self.synchronizeAction)

        self.newWorkspaceAction = QAction("Add new workspace", userActions)
        self.newWorkspaceAction.triggered.connect(self.newWorkspaceBtnClicked)
        self.userMenu.addAction(self.newWorkspaceAction)

        # Preferences
        submenu = QMenu("Preferences", self.userMenu)
        clearCacheAction = QAction("Clear Cache on logout", submenu)
        clearCacheAction.setCheckable(True)
        clearCacheAction.setChecked(p.GetBool("clearCache", False))
        clearCacheAction.triggered.connect(lambda state: p.SetBool("clearCache", state))
        submenu.addAction(clearCacheAction)
        self.userMenu.addMenu(submenu)

        a4 = QAction("Log out", userActions)
        a4.triggered.connect(self.logout)
        self.userMenu.addAction(a4)

        # Ondsel Button's menu when user not logged in
        self.guestMenu = QMenu(self.form.userBtn)
        guestActions = QActionGroup(self.guestMenu)

        a5 = QAction("Login", guestActions)
        a5.triggered.connect(self.loginBtnClicked)
        self.guestMenu.addAction(a5)

        a6 = QAction("Sign up", guestActions)
        a6.triggered.connect(self.showOndselSignUpPage)
        self.guestMenu.addAction(a6)

        # self.guestMenu.addAction(self.newWorkspaceAction)

    def isLoggedIn(self):
        return self.access_token is not None and self.apiClient is not None

    def isTokenExpired(self, token):
        expiration_time = self.getTokenExpirationTime(token)
        current_time = datetime.now()
        return current_time > expiration_time

    def setTokenExpirationTimer(self, token):
        expiration_time = self.getTokenExpirationTime(token)
        current_time = datetime.now()

        time_difference = expiration_time - current_time
        interval_milliseconds = max(0, time_difference.total_seconds() * 1000)

        # Create a QTimer that triggers only once when the token is expired
        self.token_timer = QtCore.QTimer()
        self.token_timer.setSingleShot(True)
        self.token_timer.timeout.connect(self.token_expired_handler)
        self.token_timer.start(interval_milliseconds)

    def token_expired_handler(self):
        QMessageBox.information(
            None,
            "Token Expired",
            "Your authentication token has expired, you have been logged out.",
        )

        user = None
        self.logout()

    def getTokenExpirationTime(self, token):
        try:
            decoded_token = jwt.decode(
                token,
                audience="lens.ondsel.com",
                options={"verify_signature": False, "verify_aud": False},
            )
        except ExpiredSignatureError:
            self.logout()

            self.setUIForLogin(False)
            return False
        except Exception as e:
            print(e)
            raise e
        return datetime.fromtimestamp(decoded_token["exp"])

    def setUIForLogin(self, state, user=None):
        """Toggle the visibility of UI elements based on if user is logged in"""

        if state:
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
        self.currentWorkspace = self.workspacesModel.data(index)
        self.setWorkspaceModel()

    def setWorkspaceModel(self):
        if self.isLoggedIn():
            self.currentWorkspaceModel = ServerWorkspaceModel(
                self.currentWorkspace, API_Client=self.apiClient
            )
        else:
            self.currentWorkspaceModel = LocalWorkspaceModel(self.currentWorkspace)


        # Create a workspace model and set it to the list
        # if self.apiClient is None and self.access_token is None:
        #     print("You need to login first")
        #     self.loginBtnClicked()
        #     self.enterWorkspace(index)
        #     return
        # if self.apiClient is None and self.access_token is not None:
        #     self.apiClient = APIClient(
        #         "", "", baseUrl, lensUrl, self.access_token, self.user
        #     )

        #     self.currentWorkspaceModel = ServerWorkspaceModel(
        #         self.currentWorkspace, API_Client=self.apiClient
        #     )
        # else:
        #     self.currentWorkspaceModel = LocalWorkspaceModel(self.currentWorkspace)

        self.form.workspaceNameLabel.setText(
            self.currentWorkspaceModel.getWorkspacePath()
        )

        self.form.fileList.setModel(self.currentWorkspaceModel)
        self.synchronizeAction.triggered.connect(
            self.currentWorkspaceModel.refreshModel
        )
        self.newWorkspaceAction.setVisible(False)

        self.switchView()

    def leaveWorkspace(self):
        if self.currentWorkspace is None:
            return
        self.newWorkspaceAction.setVisible(True)
        self.synchronizeAction.setVisible(False)
        self.synchronizeAction.triggered.disconnect()
        self.currentWorkspace = None
        self.currentWorkspaceModel = None
        self.form.fileList.setModel(None)
        self.switchView()
        self.form.workspaceNameLabel.setText("")
        self.form.fileDetails.setVisible(False)

    def switchView(self):
        isFileView = self.currentWorkspace is not None
        self.form.WorkspaceDetails.setVisible(isFileView)
        self.form.fileList.setVisible(isFileView)

        if self.user is None and self.workspacesModel.rowCount() == 0:
            self.form.txtExplain.setVisible(True)
            self.form.workspaceListView.setVisible(False)
        else:
            self.form.txtExplain.setVisible(False)
            self.form.workspaceListView.setVisible(not isFileView)

    def backClicked(self):
        if self.currentWorkspace is None:
            return
        subPath = self.currentWorkspaceModel.subPath

        if subPath == "":
            self.leaveWorkspace()
        else:
            self.currentWorkspaceModel.openParentFolder()
            self.form.workspaceNameLabel.setText(
                self.currentWorkspaceModel.getWorkspacePath()
            )

    def fileListDoubleClicked(self, index):
        # print("fileListDoubleClicked")

        self.currentWorkspaceModel.openFile(index)

        self.form.workspaceNameLabel.setText(
            self.currentWorkspaceModel.getWorkspacePath()
        )

    def linksListDoubleClicked(self, index):
        # print("linksListDoubleClicked")
        model = self.form.linksView.model()
        linkData = model.data(index, ShareLinkModel.EditLinkRole)

        dialog = SharingLinkEditDialog(linkData, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()
            model.update_link(index, link_properties)

    def versionClicked(self, row):
        message_box = QMessageBox()
        message_box.setWindowTitle("Confirmation")
        message_box.setText(
            "You are reverting to a backup file.\nDo you want to save the current version as new backup or discard the changes?",
        )
        message_box.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )

        # Show the dialog and retrieve the user's choice
        choice = message_box.exec_()

        if choice == QMessageBox.Cancel:
            return
        model = self.form.versionsComboBox.model()
        index = model.index(row, 0)

        idx = self.form.fileList.currentIndex()
        fileName = self.currentWorkspaceModel.data(idx, WorkSpaceModel.NameRole)
        fullFileName = f"{self.currentWorkspace['url']}/{fileName}"

        """if self.currentWorkspace["type"] == "Local":
            backupfilename = model.data(index, role=QtCore.Qt.UserRole)

            # Process the user's choice
            if choice == QMessageBox.Save:
                # make sure the document is open and get a reference
                doc = FreeCAD.open(fullFileName)

                # create a temporary copy of the backup so it isn't lost by backup policy
                temp_dir = tempfile.gettempdir()
                temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, delete=False)
                temp_file_path = temp_file.name
                temp_file.close()

                shutil.copy(backupfilename, temp_file_path)

                # Save and close the original to create the new backup
                doc.save()
                FreeCAD.closeDocument(doc.Name)

                # move the tempfile back to the original
                try:
                    shutil.move(temp_file_path, fullFileName)
                except OSError as e:
                    print(f"Error renaming file: {e}")
                # reopen the original
                doc = FreeCAD.open(fullFileName)
            elif choice == QMessageBox.Discard:
                try:
                    shutil.move(backupfilename, fullFileName)
                except OSError as e:
                    print(f"Error renaming file: {e}")
                doc = FreeCAD.open(fullFileName)
                doc.restore()
        elif self.currentWorkspace["type"] == "Ondsel":"""
        versionUniqueFileName = model.data(index, role=QtCore.Qt.UserRole)

        # Process the user's choice
        if choice == QMessageBox.Save:
            # Save and upload the current version
            doc = FreeCAD.open(fullFileName)
            doc.save()
            self.currentWorkspaceModel.uploadFile(idx)
            FreeCAD.closeDocument(doc.Name)

            # Download (and override) the required version from the server
            model.API_Client.downloadFileFromServer(versionUniqueFileName, fullFileName)

            # re-open the file
            doc = FreeCAD.open(fullFileName)
        elif choice == QMessageBox.Discard:
            # Download (and override) the required version from the server
            model.API_Client.downloadFileFromServer(versionUniqueFileName, fullFileName)

            doc = FreeCAD.open(fullFileName)
            doc.restore()
        model.refreshModel()

    def fileListClickedLoggedIn(self, file_item):
        if not file_item.is_folder and "modelId" in file_item.serverFileDict:
            self.currentModelId = file_item.serverFileDict["modelId"]

        if file_item.is_folder:
            self.form.thumbnail_label.hide()
        else:
            self.form.thumbnail_label.show()
            path = self.currentWorkspaceModel.getFullPath()
            pixmap = Utils.extract_thumbnail(f"{path}/{self.currentFileName}")
            if pixmap == None:
                pixmap = self.getServerThumbnail(
                    self.currentFileName, path, self.currentModelId
                )
                if pixmap == None:
                    pixmap = QPixmap(f"{modPath}/Resources/thumbTest.png")
            self.form.thumbnail_label.setFixedSize(pixmap.width(), pixmap.height())
            self.form.thumbnail_label.setPixmap(pixmap)
        self.form.fileNameLabel.setText(self.currentFileName)

        version_model = None
        self.links_model = None
        self.form.viewOnlineBtn.setVisible(False)
        self.form.linkDetails.setVisible(False)

        if not file_item.is_folder:
            self.form.fileDetails.setVisible(True)
            if self.currentModelId is not None:
                self.links_model = ShareLinkModel(self.currentModelId, self.apiClient)
                self.form.viewOnlineBtn.setVisible(True)
                self.form.linkDetails.setVisible(True)
                version_model = OndselVersionModel(self.currentModelId, self.apiClient)
        self.form.linksView.setModel(self.links_model)
        self.setVersionListModel(version_model)

    def fileListClicked(self, index):
        file_item = self.currentWorkspaceModel.data(index)
        self.currentFileName = file_item.name
        self.currentModelId = None
        if self.isLoggedIn():
            self.fileListClickedLoggedIn(file_item)

    def getServerThumbnail(self, fileName, path, fileId):
        # check if we have stored the thumbnail locally already.
        if not os.path.exists(f"{path}/.thumbnails"):
            os.makedirs(f"{path}/.thumbnails")
        localThumbPath = f"{path}/.thumbnails/{fileName}.png"
        if os.path.exists(localThumbPath):
            pixmap = QPixmap(localThumbPath)
        else:
            pixmap = self.currentWorkspaceModel.getServerThumbnail(fileId)
            if pixmap != None:
                pixmap.save(localThumbPath, "PNG")
        return pixmap

    def setVersionListModel(self, model):
        if model == None:
            self.form.versionsComboBox.clear()
            emptyModel = QtCore.QStringListModel()
            self.form.versionsComboBox.setModel(emptyModel)
            self.form.versionsComboBox.setVisible(False)
        else:
            self.form.versionsComboBox.setModel(model)
            self.form.versionsComboBox.setVisible(True)

    def showWorkspaceContextMenu(self, pos):
        index = self.form.workspaceListView.indexAt(pos)

        if index.isValid():
            menu = QtGui.QMenu()

            deleteAction = menu.addAction("Delete")
            deleteAction.setEnabled(self.apiClient is not None)

            action = menu.exec_(self.form.workspaceListView.viewport().mapToGlobal(pos))

            if action == deleteAction:
                result = QtGui.QMessageBox.question(
                    self,
                    "Delete Workspace",
                    "Are you sure you want to delete this workspace?",
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                )
                if result == QtGui.QMessageBox.Yes:
                    self.apiClient.deleteWorkspace(
                        self.workspacesModel.data(index)["_id"]
                    )
                    self.workspacesModel.refreshModel()
        else:
            menu = QtGui.QMenu()
            addAction = menu.addAction("Add workspace")
            addAction.setEnabled(self.apiClient is not None)

            action = menu.exec_(self.form.workspaceListView.viewport().mapToGlobal(pos))

            if action == addAction:
                self.newWorkspaceBtnClicked()

    def showFileContextMenu(self, pos):
        index = self.form.fileList.indexAt(pos)
        file_item = self.currentWorkspaceModel.data(index)
        if file_item is None:
            return

        menu = QtGui.QMenu()
        openOnlineAction = menu.addAction("View in Lens")
        uploadAction = menu.addAction("Upload to Lens")
        downloadAction = menu.addAction("Download from Lens")
        if self.isLoggedIn():
            if file_item.status == "Server only":
                uploadAction.setEnabled(False)
            if file_item.status == "Untracked":
                downloadAction.setEnabled(False)
            if file_item.ext not in [".fcstd", ".obj"]:
                openOnlineAction.setEnabled(False)
        else:
            uploadAction.setEnabled(False)
            downloadAction.setEnabled(False)
            openOnlineAction.setEnabled(False)
        menu.addSeparator()
        deleteAction = menu.addAction("Delete File")

        action = menu.exec_(self.form.fileList.viewport().mapToGlobal(pos))

        if action == deleteAction:
            result = QtGui.QMessageBox.question(
                self.form.fileList,
                "Delete File",
                "Are you sure you want to delete this file?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            )
            if result == QtGui.QMessageBox.Yes:
                self.currentWorkspaceModel.deleteFile(index)
        if action == openOnlineAction:
            self.openModelOnline()
        elif action == downloadAction:
            self.currentWorkspaceModel.downloadFile(index)
        elif action == uploadAction:
            self.currentWorkspaceModel.uploadFile(index)
            self.form.versionsComboBox.model().refreshModel()

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
        linkId = model.data(index, ShareLinkModel.UrlRole)
        url = model.compute_url(linkId)
        forum_iframe = model.compute_forum_iframe(linkId)

        # Create a custom dialog
        dialog = QtGui.QDialog(
            self.form, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint
        )  # Set dialog as a popup without title bar
        dialog.setWindowTitle("Share Options")
        dialog.setWindowModality(QtCore.Qt.NonModal)  # Set dialog to non-modal

        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel("Choose an option for sharing:")
        layout.addWidget(label)

        # Add custom buttons with desired tooltips
        model_url_button = QtGui.QPushButton("Model URL")
        model_url_button.setToolTip(
            "This is the URL where anyone with the link can view your model through Ondsel Lens."
        )

        forum_iframe_button = QtGui.QPushButton("FreeCAD forum")
        forum_iframe_button.setToolTip(
            "This is a shortcode that you can paste in FreeCAD forum posts to embed a view of your model in your post."
        )

        # Add buttons to the layout
        layout.addWidget(model_url_button)
        layout.addWidget(forum_iframe_button)

        # Connect button actions
        model_url_button.clicked.connect(lambda: self.copyToClipboard(url))
        forum_iframe_button.clicked.connect(lambda: self.copyToClipboard(forum_iframe))

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

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        print("Link copied!")

    def editShareLinkClicked(self, index):
        model = self.form.linksView.model()
        linkData = model.data(index, ShareLinkModel.EditLinkRole)

        dialog = SharingLinkEditDialog(linkData, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()
            model.update_link(index, link_properties)

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
            model.delete_link(linkId)

    def addShareLink(self):
        dialog = SharingLinkEditDialog(None, self)

        if dialog.exec_() == QtGui.QDialog.Accepted:
            link_properties = dialog.getLinkProperties()

            self.form.linksView.model().add_new_link(link_properties)

    def openModelOnline(self):
        url = ondselUrl

        if self.currentModelId is not None:
            url = f"{lensUrl}model/{self.currentModelId}"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def openPreferences(self):
        print("Preferences clicked")

    def ondselAccount(self):
        url = f"{lensUrl}login"
        QtGui.QDesktopServices.openUrl(url)

    def showOndselSignUpPage(self):
        url = f"{lensUrl}signup"
        QtGui.QDesktopServices.openUrl(url)

    def loginBtnClicked(self):
        while True:
            # Show a login dialog to get the user's email and password
            dialog = LoginDialog()
            if dialog.exec_() == QtGui.QDialog.Accepted:
                email, password = dialog.get_credentials()
                try:
                    self.apiClient = APIClient(email, password, baseUrl, lensUrl)
                    self.apiClient._authenticate()
                except CustomAuthenticationError as e:
                    print("Handling authentication error:", str(e))
                    continue  # Present the login dialog again if authentication fails
                # Check if the request was successful (201 status code)
                if self.apiClient.access_token is not None:
                    self.user = self.apiClient.user
                    loginData = {
                        "accessToken": self.apiClient.access_token,
                        "user": self.user,
                    }
                    p.SetString("loginData", json.dumps(loginData))

                    self.access_token = self.apiClient.access_token

                    self.setUIForLogin(True, self.apiClient.user)
                    self.leaveWorkspace()
                    self.workspacesModel.refreshModel()
                    self.switchView()

                    # Set a timer to logout when token expires.
                    self.setTokenExpirationTimer(self.access_token)
                else:
                    print("Authentication failed")
                break
            else:
                break  # Exit the login loop if the dialog is canceled

    def logout(self):
        self.setUIForLogin(False)
        p.SetString("loginData", "")
        self.access_token = None
        self.apiClient = None

        self.setWorkspaceModel()

        # self.leaveWorkspace()

        # self.workspacesModel.removeOndselWorkspaces()

    def timerTick(self):
        if self.currentWorkspace != None:
            self.currentWorkspaceModel.refreshModel()
        else:
            self.workspacesModel.refreshModel()

    def addCurrentFile(self):
        # Save current file on the server.
        doc = FreeCAD.ActiveDocument

        if doc is None:
            QMessageBox.information(
                self,
                "No FreeCAD File Opened",
                "You don't have any FreeCAD file opened now.",
            )
            return
        # Get the default name of the file from the document
        default_name = doc.Label + ".FCStd"
        default_path = self.currentWorkspaceModel.getFullPath()
        default_file_path = Utils.joinPath(default_path, default_name)

        # Open a dialog box for the user to select a file location and name
        file_name, _ = QtGui.QFileDialog.getSaveFileName(
            self, "Save File", default_file_path, "FreeCAD file (*.fcstd)"
        )

        if file_name:
            # Make sure the file has the correct extension
            if not file_name.lower().endswith(".fcstd"):
                file_name += ".FCStd"
            # Save the file
            FreeCAD.Console.PrintMessage(f"Saving document to file: {file_name}\n")
            doc.saveAs(file_name)

    def addFileBtnClicked(self):
        # open file browser dialog to select files to copy
        selectedFiles, _ = QtGui.QFileDialog.getOpenFileNames(
            None,
            "Select Files",
            os.path.expanduser("~"),
            "All Files (*);;Text Files (*.txt)",
        )

        # copy selected files to destination folder
        for fileUrl in selectedFiles:
            fileName = os.path.basename(fileUrl)

            destFileUrl = Utils.joinPath(
                self.currentWorkspaceModel.getFullPath(), fileName
            )

            if Utils.isOpenableByFreeCAD(fileName):
                try:
                    shutil.copy(fileUrl, destFileUrl)
                except:
                    QtGui.QMessageBox.warning(
                        None, "Error", "Failed to copy file " + fileName
                    )

    def newWorkspaceBtnClicked(self):
        if self.apiClient is None and self.access_token is None:
            print("You need to login first")
            self.loginBtnClicked()
            return
        if self.apiClient is None and self.access_token is not None:
            self.apiClient = APIClient(
                "", "", baseUrl, lensUrl, self.access_token, self.user
            )

        dialog = NewWorkspaceDialog()
        # Show the dialog and wait for the user to close it
        if dialog.exec_() == QtGui.QDialog.Accepted:
            workspaceName = dialog.nameEdit.text()
            workspaceDesc = dialog.descEdit.toPlainText()

            personal_organisation = None
            for organization in self.user["organizations"]:
                if organization.get("name") == "Personal":
                    personal_organisation = organization.get("_id")
                    break

            if personal_organisation is None:
                return

            self.apiClient.createWorkspace(
                workspaceName, workspaceDesc, personal_organisation
            )

            # workspaceType = "Ondsel"
            # workspaceId = result["_id"]
            # workspaceUrl = cachePath + workspaceId #workspace id.
            # workspaceRootDir = result["rootDirectory"]

            self.workspacesModel.refreshModel()

            # # Determine workspace type and get corresponding values
            # if dialog.localRadio.isChecked():
            #     workspaceType = "Local"
            #     workspaceUrl = dialog.localFolderLabel.text()
            # elif dialog.ondselRadio.isChecked():
            #     workspaceType = "Ondsel"
            #     workspaceUrl = cachePath + dialog.nameEdit.text()
            # else:
            #     workspaceType = "External"
            #     workspaceUrl = dialog.externalServerEdit.text()
            # Update workspaceListWidget with new workspace

    def get_server_package_file(self):
        response = requests.get(remote_package_url)
        if response.status_code == 200:
            return response.text
        return None

    def get_local_package_file(self):
        try:
            with open(local_package_path, "r") as file_:
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

    def check_for_update(self):
        local_version = self.get_version_from_package_file(
            self.get_local_package_file()
        )
        remote_version = self.get_version_from_package_file(
            self.get_server_package_file()
        )

        if local_version and remote_version and local_version != remote_version:
            self.form.updateAvailable.setUrl(remote_changelog_url)
            self.form.updateAvailable.setText(
                f"Ondsel Lens v{remote_version} available!"
            )
            self.form.updateAvailable.setToolTip(
                f"Click to see the change-log of Ondsel Lens v{remote_version} in your browser.</a>"
            )

            self.form.updateAvailable.show()


class NewWorkspaceDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(NewWorkspaceDialog, self).__init__(parent)
        self.setWindowTitle("Add Workspace")
        self.setModal(True)

        layout = QtGui.QVBoxLayout()

        # Radio buttons for selecting workspace type
        # self.localRadio = QtGui.QRadioButton("Local")
        # self.ondselRadio = QtGui.QRadioButton("Ondsel Server")
        # self.ondselRadio.setToolTip(
        #     "Ondsel currently supports only one workspace that is added automatically on login."
        # )
        # self.ondselRadio.setEnabled(False)
        # self.externalRadio = QtGui.QRadioButton("External Server")
        # self.externalRadio.setToolTip(
        #     "Currently external servers support is not implemented."
        # )
        # self.externalRadio.setEnabled(False)

        # button_group = QtGui.QButtonGroup()
        # button_group.addButton(self.localRadio)
        # button_group.addButton(self.ondselRadio)
        # button_group.addButton(self.externalRadio)

        # group_box = QtGui.QGroupBox("type")
        # group_box_layout = QtGui.QHBoxLayout()
        # group_box_layout.addWidget(self.localRadio)
        # group_box_layout.addWidget(self.ondselRadio)
        # group_box_layout.addWidget(self.externalRadio)
        # group_box.setLayout(group_box_layout)

        # Workspace Name
        self.nameLabel = QtGui.QLabel("Name")
        self.nameEdit = QtGui.QLineEdit()
        nameHlayout = QtGui.QHBoxLayout()
        nameHlayout.addWidget(self.nameLabel)
        nameHlayout.addWidget(self.nameEdit)

        # Workspace description
        self.descLabel = QtGui.QLabel("Description")
        self.descEdit = QtGui.QTextEdit()

        # # Widgets for local workspace type
        # self.localFolderLabel = QtGui.QLineEdit("")
        # self.localFolderEdit = QtGui.QPushButton("Select folder")
        # self.localFolderEdit.clicked.connect(self.show_folder_picker)
        # h_layout = QtGui.QHBoxLayout()
        # h_layout.addWidget(self.localFolderLabel)
        # h_layout.addWidget(self.localFolderEdit)

        # # Widgets for external server workspace type
        # self.externalServerLabel = QtGui.QLabel("Server URL")
        # self.externalServerEdit = QtGui.QLineEdit()

        # Add widgets to layout
        # layout.addWidget(group_box)
        layout.addLayout(nameHlayout)
        layout.addWidget(self.descLabel)
        layout.addWidget(self.descEdit)
        # layout.addLayout(h_layout)
        # layout.addWidget(self.externalServerLabel)
        # layout.addWidget(self.externalServerEdit)

        # Connect radio buttons to updateDialog function
        # self.localRadio.toggled.connect(self.updateDialog)
        # self.ondselRadio.toggled.connect(self.updateDialog)
        # self.externalRadio.toggled.connect(self.updateDialog)
        # self.localRadio.setChecked(True)

        # Add OK and Cancel buttons
        buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Add layout and buttons to dialog
        self.setLayout(layout)
        layout.addWidget(buttonBox)

    # Function to update the dialog when the workspace type is changed
    def updateDialog(self):
        pass
        # if self.ondselRadio.isChecked():
        #     self.nameLabel.setText("ondsel.com/")
        # else:
        #     self.nameLabel.setText("Name")
        # self.localFolderLabel.setVisible(self.localRadio.isChecked())
        # self.localFolderEdit.setVisible(self.localRadio.isChecked())

        # self.externalServerLabel.setVisible(self.externalRadio.isChecked())
        # self.externalServerEdit.setVisible(self.externalRadio.isChecked())

    # def show_folder_picker(self):
    #     options = QtGui.QFileDialog.Options()
    #     options |= QtGui.QFileDialog.ShowDirsOnly
    #     folder_url = QtGui.QFileDialog.getExistingDirectory(
    #         self, "Select Folder", options=options
    #     )
    #     if folder_url:
    #         self.localFolderLabel.setText(folder_url)

    # def okClicked(self):
    #    pass
    # if self.localRadio.isChecked():
    #    if os.path.isdir(self.localFolderLabel.text()):
    #        self.accept()
    #    else:
    #        result = QtGui.QMessageBox.question(
    #            self,
    #            "Wrong URL",
    #            "The URL you entered is not correct.",
    #            QtGui.QMessageBox.Ok,
    #        )


class SharingLinkEditDialog(QtGui.QDialog):
    def __init__(self, linkProperties=None, parent=None):
        super(SharingLinkEditDialog, self).__init__(parent)

        # Load the UI from the .ui file
        self.dialog = Gui.PySideUic.loadUi(modPath + "/SharingLinkEditDialog.ui")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.dialog)
        self.setLayout(layout)

        self.dialog.okBtn.clicked.connect(self.accept)
        self.dialog.cancelBtn.clicked.connect(self.reject)

        if linkProperties is None:
            self.linkProperties = {
                "description": "",
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
        else:
            self.linkProperties = linkProperties
        self.setLinkProperties()

    def setLinkProperties(self):
        self.dialog.linkName.setText(self.linkProperties["description"])
        self.dialog.canViewModelAttributesCheckBox.setChecked(
            self.linkProperties["canViewModelAttributes"]
        )
        self.dialog.canUpdateModelCheckBox.setChecked(
            self.linkProperties["canUpdateModel"]
        )
        self.dialog.canExportFCStdCheckBox.setChecked(
            self.linkProperties["canExportFCStd"]
        )
        self.dialog.canExportSTEPCheckBox.setChecked(
            self.linkProperties["canExportSTEP"]
        )
        self.dialog.canExportSTLCheckBox.setChecked(self.linkProperties["canExportSTL"])
        self.dialog.canExportOBJCheckBox.setChecked(self.linkProperties["canExportOBJ"])

    def getLinkProperties(self):
        self.linkProperties["description"] = self.dialog.linkName.text()
        self.linkProperties[
            "canViewModelAttributes"
        ] = self.dialog.canViewModelAttributesCheckBox.isChecked()
        self.linkProperties[
            "canUpdateModel"
        ] = self.dialog.canUpdateModelCheckBox.isChecked()
        self.linkProperties[
            "canExportFCStd"
        ] = self.dialog.canExportFCStdCheckBox.isChecked()
        self.linkProperties[
            "canExportSTEP"
        ] = self.dialog.canExportSTEPCheckBox.isChecked()
        self.linkProperties[
            "canExportSTL"
        ] = self.dialog.canExportSTLCheckBox.isChecked()
        self.linkProperties[
            "canExportOBJ"
        ] = self.dialog.canExportOBJCheckBox.isChecked()

        return self.linkProperties


class LoginDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")

        self.email_label = QtGui.QLabel("Email:")
        self.email_input = QtGui.QLineEdit()

        self.password_label = QtGui.QLabel("Password:")
        self.password_input = QtGui.QLineEdit()
        self.password_input.setEchoMode(QtGui.QLineEdit.Password)

        self.login_button = QtGui.QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.login_button.setEnabled(False)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

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


wsv = WorkspaceView()
