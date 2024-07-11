import FreeCAD
import register_lens_handler

# param_group = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Start")
# param_group.SetBool("ShowOnStartup", False)

FreeCAD.Console.PrintMessage("Init Lens\n")

register_lens_handler.register_lens_handler()
