import FreeCAD
import FreeCADGui as Gui

import Utils

from PySide import QtGui
from PySide import QtWidgets

NAME_COMMAND = "OndselLens_OndselLens"
ACCEL = "Ctrl+L"
NAME_COMMAND_START = "Start_Start"


class LensCommand:
    def Activated(self):
        open_mdi_view()

    def GetResources(self):
        return {
            "Pixmap": Utils.icon_ondsel,
            "Accel": "Ctrl+L",
            "MenuText": "Ondsel Lens Addon",
            "ToolTip": "Show the Ondsel Lens Addon in an MDI view.",
        }


class LensWorkbenchManipulator:
    def modifyMenuBar(self):
        return [{"insert": NAME_COMMAND, "menuItem": "Std_WhatsThis", "after": ""}]

    def modifyToolBars(self):
        return [{"append": NAME_COMMAND, "toolBar": "Help"}]


# def open_mdi_view():
#     import PySide.QtWidgets as QtWidgets
#     import WorkspaceView

#     main_window = Gui.getMainWindow()
#     FreeCAD.Console.PrintMessage("1\n")
#     FreeCAD.Console.PrintMessage("1a\n")

#     mdi_area = main_window.findChild(QtWidgets.QMdiArea)
#     wsv = mdi_area.findChild(WorkspaceView.WorkspaceView, "workspaceView")
#     if wsv:
#         subwindow = wsv.parent()
#         mdi_area.setActiveSubWindow(subwindow)
#     else:
#         if True:
#             mw = QtWidgets.QMainWindow()
#             WorkspaceView.wsv = WorkspaceView.WorkspaceView(mw)
#             # mw.setCentralWidget(WorkspaceView.wsv)
#             # subwindow = QtWidgets.QMdiSubWindow()
#             # WorkspaceView.wsv.setParent(subwindow)
#             # subwindow.setObjectName("subwindow")
#             # subwindow.setWidget(WorkspaceView.wsv)
#             window = main_window.addWindow(mw)
#             #window.setWindowIcon(QtGui.QIcon(Utils.icon_ondsel))
#             #window.showMaximized()
#         else:
#             WorkspaceView.wsv = WorkspaceView.WorkspaceView()
#             FreeCAD.Console.PrintMessage("3\n")
#             subwindow = mdi_area.addSubWindow(WorkspaceView.wsv)
#             subwindow.setWindowTitle("Ondsel Lens")
#             subwindow.setWindowIcon(QtGui.QIcon(Utils.icon_ondsel))
#             subwindow.showMaximized()


def find_subwindow():
    main_window = Gui.getMainWindow()
    subwindows = main_window.findChildren(QtWidgets.QMdiSubWindow)
    for subwindow in subwindows:
        if subwindow.widget().centralWidget().objectName() == "WorkspaceView":
            return subwindow

    return None


def open_mdi_view():
    import PySide.QtWidgets as QtWidgets
    import WorkspaceView

    main_window = Gui.getMainWindow()
    subwindow = find_subwindow()
    if subwindow:
        mdi_area = main_window.findChild(QtWidgets.QMdiArea)
        mdi_area.setActiveSubWindow(subwindow)
    else:
        if WorkspaceView.wsv:
            del WorkspaceView.wsv
        WorkspaceView.wsv = WorkspaceView.WorkspaceView()
        main_window.addWindow(WorkspaceView.wsv)
        subwindow = find_subwindow()
        if subwindow:
            subwindow.setWindowTitle("Ondsel Lens")
            subwindow.setWindowIcon(QtGui.QIcon(Utils.icon_ondsel))
            subwindow.showMaximized()


# def open_mdi_view():
#     pass


Gui.addCommand("OndselLens_OndselLens", LensCommand())
Gui.addWorkbenchManipulator(LensWorkbenchManipulator())
