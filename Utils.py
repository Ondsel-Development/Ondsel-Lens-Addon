# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import os
import FreeCAD

def joinPath(first, second):
    return os.path.join(first, second).replace("\\", "/")
    #return os.path.normpath(os.path.join(first, second))

def isOpenableByFreeCAD(filename):

    "check if FreeCAD can handle this file type"

    if os.path.isdir(filename):
        return False
    if os.path.basename(filename)[0] == ".":
        return False
    extensions = [key.lower() for key in FreeCAD.getImportType().keys()]
    ext = os.path.splitext(filename)[1].lower()
    if ext:
        if ext[0] == ".":
            ext = ext[1:]
    if ext in extensions:
        return True
    return False