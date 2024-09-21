from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (
    QMainWindow,
    QMdiArea,
    QTabWidget,
    QTextEdit,
    QWidget,
    QSizePolicy,
    QMdiSubWindow,
)

from CADAccess.MockFreeCAD import FreeCAD


class PySideUicClass:
    """this is a ui manipulation class for the MDI. At least, what is what we are using it for."""

    def __init__(self, main_window, mdi_area):
        self.main_window = main_window
        self.mdi_area = mdi_area

    def loadUi(self, ui_path):
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        newPanel = loader.load(ui_file)
        return newPanel

    def addWindowToMdi(self, new_window: QWidget):
        newTitle = new_window.windowTitle()
        window = QMainWindow(self.mdi_area)
        window.setWindowTitle(newTitle)
        window.setCentralWidget(new_window)
        self.mdi_area.addSubWindow(window)
        window.show()


class FreeCADGuiClass:
    def __init__(self):
        self.starting_commands = []
        self.starting_manipulations = []
        self.main_window = None
        self.mdi = None
        self.PySideUic = None
        self.report_console = None

    def set_main_window_ref(self, parent_window):
        self.main_window = parent_window.findChildren(QMainWindow)[0]
        self.mdi = self.main_window.findChildren(QMdiArea)[0]
        self.mdi.setViewMode(QMdiArea.TabbedView)
        self.mdi.setTabsClosable(True)
        self.mdi.setTabPosition(QTabWidget.TabPosition.South)
        self.PySideUic = PySideUicClass(self.main_window, self.mdi)
        self.report_console = parent_window.findChildren(QTextEdit)[0]
        FreeCAD.Console.setConsoleWidget(self.report_console)
        FreeCAD.Console.print_shallow("Report View")
        # add functions not normally part of QMainWindow:
        self.main_window.addWindow = self.PySideUic.addWindowToMdi

    def addCommand(self, key, todo):
        self.starting_commands.append((key, todo))

    def addWorkbenchManipulator(self, manipulation):
        self.starting_manipulations.append(manipulation)

    def getMainWindow(self):
        return self.main_window


FreeCADGui = FreeCADGuiClass()
