import sys

from PySide2.QtWidgets import QApplication

from _mock_environment.main import MainWindow

app = QApplication(sys.argv)

with open("_mock_environment/theme/OpenDark.qss", "r") as f:
    _style = f.read()
    app.setStyleSheet(_style)

window = MainWindow()
window.prep_operations()
window.begin_ondsel_lens()
app.exec_()
