from PySide2.QtWidgets import QTextEdit

LEVELS_TO_SHOW_ON_REPORT_VIEW = ["warning", "info", "error", "all"]  # all is a "fake" level


class MockConsole:
    def __init__(self):
        self.report_view = None

    def PrintLog(self, arg: str) -> None:
        print("(fc-console-log)", arg)
        self._consider_display(arg, "debug")

    def PrintMessage(self, arg: str) -> None:
        print("(fc-console-msg)", arg)
        self._consider_display(arg, "info")

    def PrintWarning(self, arg: str) -> None:
        print("(fc-console-warn)", arg)
        self._consider_display(arg, "warning")

    def PrintError(self, arg: str) -> None:
        print("(fc-console-err)", arg)
        self._consider_display(arg, "error")

    def setConsoleWidget(self, widget: QTextEdit):
        """this is a mock-only routine; creates connection to ReportView UI console"""
        self.report_view = widget

    def _consider_display(self, arg: str, level: str) -> None:
        if level in LEVELS_TO_SHOW_ON_REPORT_VIEW:
            if self.report_view is not None:
                if level != "all":
                    self.report_view.insertPlainText("\n")
                self.report_view.insertPlainText(arg)

    def print_shallow(self, arg: str) -> None:
        """this is a mock-only routine; prints to the console without decoration or logging"""
        self._consider_display(arg, "all")
