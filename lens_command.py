import Utils
import WorkspaceView


class LensCommand:
    def GetResources(self):
        return {
            "Pixmap": Utils.icon_ondsel_path_disconnected,
            "Accel": "Ctrl+L",
            "MenuText": Utils.LENS_TOOLBARITEM_TEXT,
            "ToolTip": "Show the Ondsel Lens Addon in an MDI view.",
        }
    
    def Activated(self):
        return

    def IsActive(self):
        return True

class LensWorkbenchManipulator:
    def modifyMenuBar(self):
        return [{"insert": Utils.NAME_COMMAND, "menuItem": "Std_WhatsThis", "after": ""}]

    def modifyToolBars(self):
        return [
          {"append": Utils.NAME_COMMAND, "toolBar": "File"}
        ]
