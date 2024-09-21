from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
import FreeCAD
import FreeCADGui

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()
        ui_file = QFile("_mock_environment/MockFreeCADGui.ui")
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self).show()
        ui_file.close()

    def prep_operations(self):
        FreeCADGui.set_main_window_ref(self)
        self.add_false_start_panel()

    def begin_ondsel_lens(self):
        import Init
        import InitGui

    def post_operations(self):
        pass

    def add_false_start_panel(self):
        start_panel = FreeCADGui.PySideUic.loadUi("_mock_environment/MockStartPanel.ui")
        FreeCADGui.PySideUic.addWindowToMdi(start_panel)
