# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2023 Ondsel                                           *
# *                                                                     *
# ***********************************************************************

import os
import math
import re
import logging

import zipfile
import shutil
from urllib.parse import urlparse

from PySide.QtGui import QPixmap
from PySide.QtCore import Qt

import FreeCAD

mod_path = os.path.dirname(__file__).replace("\\", "/")
icon_path = f"{mod_path}/Resources/icons/"
local_package_path = f"{mod_path}/package.xml"
icon_ondsel = icon_path + "OndselWorkbench.svg"

DEBUG_LEVEL = logging.INFO


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


class __OndselEnv:
    """
    this class allows for specific OS environments, such as in docker images, to
    have special operating parameters. It is also useful for testing as one
    can SET these vars locally on your own machine.
    However, typical users will NOT have the `ONDSEL_` variables set, so make sure
    the ".get" defaults are what you expect for production end-user usage.

    In Linux, a local .env file can be used with:

        set -a; . ./.env; set +a

    prior to launching FreeCAD / OndselES.

    For consistency, please use the `env` singleton declared just below. aka:

        lens_site_base = Utils.env.lens_url
    """

    def __init__(self):
        self.lens_url = os.environ.get("ONDSEL_LENS_URL", "https://lens.ondsel.com/")
        self.api_url = os.environ.get("ONDSEL_API_URL", "https://lens-api.ondsel.com/")
        self.about_url = os.environ.get("ONDSEL_ABOUT_URL", "https://www.ondsel.com/")


env = __OndselEnv()


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

                return pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)

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


def getFileNameFromURL(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.split("/")[-1]


def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(DEBUG_LEVEL)
    handler = FreeCADHandler()
    if DEBUG_LEVEL >= logging.INFO:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:
        formatter = logging.Formatter("%(levelname)s: %(name)s:%(lineno)d %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def createBackup(pathFile, extension=".ondsel-lens.bak"):
    if os.path.exists(pathFile):
        pathFileBak = pathFile + extension
        shutil.copyfile(pathFile, pathFileBak)
        return pathFileBak
    else:
        raise FileNotFoundError(f"File not found: {pathFile}")


def get_addon_version():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_xml_file = "package.xml"
    path_package_file = os.path.join(current_dir, package_xml_file)

    with open(path_package_file, "r") as file:
        package_xml_content = file.read()

    return re.search(r"<version>(.*?)<\/version>", package_xml_content).group(1)
