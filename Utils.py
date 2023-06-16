# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import os
import FreeCAD
import zipfile
from PySide2.QtGui import QPixmap
modPath = os.path.dirname(__file__).replace("\\", "/")

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
    return ext in extensions

def extract_thumbnail(file_path):
    if os.path.exists(file_path):
        try:
            # Open the FCStd file as a zip archive
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Read the contents of the thumbnail image file
                thumbnail_data = zip_ref.read('thumbnails/Thumbnail.png')

                # Create a QPixmap from the thumbnail data
                pixmap = QPixmap()
                pixmap.loadFromData(thumbnail_data)

                return pixmap

        except (zipfile.BadZipFile, KeyError):
            # Handle the case where the thumbnail file doesn't exist
            return None
    else:
        # If file doesn't exist then the file is on the server only. We could fetch the server thumbnail.
        return None