from os.path import expanduser
from .MockFreeCAD import FreeCADClass

_inst = FreeCADClass()
ParamGet = _inst.ParamGet
ConfigGet = _inst.ConfigGet
Version = _inst.Version

def getUserCachePath():
    return str(expanduser("~/.cache/Ondsel/Cache"))

def getUserConfigDir():
    return str(expanduser("~/.config/Ondsel"))
