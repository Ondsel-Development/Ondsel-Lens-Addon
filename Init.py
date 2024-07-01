import FreeCAD

param_group = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Start")
param_group.SetBool("ShowOnStartup", False)

FreeCAD.Console.PrintMessage("Init Lens\n")
