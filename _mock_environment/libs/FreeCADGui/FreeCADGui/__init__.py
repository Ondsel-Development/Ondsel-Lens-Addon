from .MockFreeCADGui import FreeCADGuiClass

_inst = FreeCADGuiClass()

set_main_window_ref = _inst.set_main_window_ref

# method mimics:
addCommand = _inst.addCommand
addWorkbenchManipulator = _inst.addWorkbenchManipulator
getMainWindow = _inst.getMainWindow

# property mimics:
def __getattr__(name):
    if name == 'PySideUic':
        return _inst.PySideUic
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
