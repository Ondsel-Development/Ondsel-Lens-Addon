# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import os
import FreeCAD
import zipfile
import math
import logging
from PySide2.QtGui import QPixmap

modPath = os.path.dirname(__file__).replace("\\", "/")

DEBUG_LEVEL = logging.DEBUG


class FreeCADHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record) + "\n"
        c = FreeCAD.Console
        if record.levelno >= logging.ERROR:
            c.PrintError(msg)
        elif record.levelno >= logging.WARNING:
            c.PrintWarning(msg)
        else:
            c.PrintMessage(msg)


def joinPath(first, second):
    return os.path.join(first, second).replace("\\", "/")
    # return os.path.normpath(os.path.join(first, second))


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
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                # Read the contents of the thumbnail image file
                thumbnail_data = zip_ref.read("thumbnails/Thumbnail.png")

                # Create a QPixmap from the thumbnail data
                pixmap = QPixmap()
                pixmap.loadFromData(thumbnail_data)

                return pixmap

        except (zipfile.BadZipFile, KeyError):
            # Handle the case where the thumbnail file doesn't exist
            return None
    else:
        # If file doesn't exist then the file is on the server only. We could fetch the
        # server thumbnail.
        return None


def getFileUpdatedAt(file_path):
    "Returns the modified time in milliseconds"
    return math.floor(os.path.getmtime(file_path) * 1000)


def getFileCreatedAt(file_path):
    "Returns the created time in milliseconds"
    return math.floor(os.path.getctime(file_path) * 1000)


def setFileModificationTimes(file_path, updatedAt, createdAt):
    """
    Set the modified and created time for a file

    The parameters createdAt and updatedAt are in milliseconds,
    whereas os.utime expects a float in seconds
    """
    os.utime(file_path, (createdAt / 1000.0, updatedAt / 1000.0))


def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(DEBUG_LEVEL)
    handler = FreeCADHandler()
    formatter = logging.Formatter("%(levelname)s: %(name)s:%(lineno)d %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
