import Utils
import WorkspaceView
import FreeCAD
import FreeCADGui as Gui
from PySide import QtGui
from PySide import QtWidgets


class LensCommand:
    def GetResources(self):
        return {
            "Pixmap": Utils.icon_ondsel_path_disconnected,
            "Accel": "Ctrl+L",
            "MenuText": Utils.LENS_TOOLBARITEM_TEXT,
            "ToolTip": "Show the Ondsel Lens Addon in an MDI view.",
        }
    
    def Activated(self):
        start_mdi_tab()

    def IsActive(self):
        return True

class LensWorkbenchManipulator:
    def modifyMenuBar(self):
        return [{"insert": Utils.NAME_COMMAND, "menuItem": "Std_WhatsThis", "after": ""}]

    def modifyToolBars(self):
        return [
          {"append": Utils.NAME_COMMAND, "toolBar": "File"}
        ]


def find_subwindow(main_window):
    from PySide import QtWidgets
    subwindows = main_window.findChildren(QtWidgets.QMdiSubWindow)
    for subwindow in subwindows:
        if subwindow.widget().centralWidget().objectName() == "WorkspaceView":
            return subwindow
    return None

def start_mdi_tab():
    main_window = Gui.getMainWindow()
    subwindow = find_subwindow(main_window)
    if subwindow:
        mdi_area = main_window.findChild(QtWidgets.QMdiArea)
        mdi_area.setActiveSubWindow(subwindow)
    else:
        if WorkspaceView.wsv:
            del WorkspaceView.wsv
        WorkspaceView.wsv = WorkspaceView.WorkspaceView(main_window)
        main_window.addWindow(WorkspaceView.wsv)
        subwindow = find_subwindow(main_window)
        if subwindow:
            subwindow.setWindowTitle("Ondsel Lens")
            subwindow.setWindowIcon(QtGui.QIcon(Utils.icon_ondsel_path_connected))
            subwindow.showMaximized()
