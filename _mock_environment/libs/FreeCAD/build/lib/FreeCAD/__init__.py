from os.path import expanduser
from .MockFreeCAD import FreeCADClass

_inst = FreeCADClass()

# method mimics:
ParamGet = _inst.ParamGet
ConfigGet = _inst.ConfigGet
Version = _inst.Version
GuiUp = _inst.GuiUp

# property mimics
Console = (
    _inst.Console
)  # this is a property set only at __init__, so a direct ref should be safe

# static equivalent
def getUserCachePath():
    return str(expanduser("~/.cache/Ondsel/Cache"))


def getUserConfigDir():
    return str(expanduser("~/.config/Ondsel"))
