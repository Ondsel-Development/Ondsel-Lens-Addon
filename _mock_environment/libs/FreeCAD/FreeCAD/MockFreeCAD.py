from .MockConsole import MockConsole
from .MockParameters import MockParameters


class FreeCADClass:
    Console = MockConsole()
    VERSION = [
        "2024",
        "3",
        "0",
        "38021 (Git)",
        "https://github.com/Ondsel-Development/FreeCAD flavor",
        "2024/07/02 00:18:49",
        "flavor",
        "a34043c4fa4efa3c871e376a4e1536dcdeb86ebc",
    ]

    def __init__(self):
        self.parameters = MockParameters()
        self.parameters.SetDict(
            "User parameter:BaseApp/Preferences/Mod/Start", MockParameters()
        )
        self.parameters.SetDict("User parameter:BaseApp/Ondsel", MockParameters())
        self.configs = {"ExeVendor": "Ondsel"}

    def ParamGet(self, name=None, default=None):
        if name is None:
            return self.parameters
        return self.parameters._Get(name, default)

    def ConfigGet(self, name=None, default=None):
        if name in self.configs.keys():
            return self.configs[name]
        return default

    def Version(self):
        return self.VERSION
