# SPDX-FileCopyrightText: 2023 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

import inspect
import os
import math
import re
import logging

from urllib.parse import urlparse
import zipfile
import shutil
from contextlib import contextmanager
from urllib.parse import urlparse
import requests

from PySide.QtGui import QPixmap, QCursor
from PySide.QtCore import Qt
from PySide.QtWidgets import QApplication

import FreeCAD

mod_path = os.path.dirname(__file__).replace("\\", "/")
icon_path = f"{mod_path}/Resources/icons/"
local_package_path = f"{mod_path}/package.xml"
icon_ondsel_path_connected = icon_path + "OndselWorkbench.svg"
icon_ondsel_path_disconnected = icon_path + "OndselWorkbench-disconnected.svg"

PARAM_GROUP = "User parameter:BaseApp/Ondsel"

URL_SCHEME = "ondsel"

DEBUG_LEVEL = logging.INFO

NAME_COMMAND = "OndselLens_OndselLens"
ACCEL = "Ctrl+L"
NAME_COMMAND_START = "Start_Start"
LENS_TOOLBARITEM_TEXT = "Ondsel Lens Addon"

SIZE_PIXMAP = 128


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
        self.debug_level = os.environ.get("ONDSEL_DEBUG_LEVEL", "info")

    def get_debug_level(self):
        if self.debug_level == "info":
            return logging.INFO
        elif self.debug_level == "debug":
            return logging.DEBUG
        elif self.debug_level == "error":
            return logging.ERROR
        elif self.debug_level == "warning":
            return logging.WARNING
        else:
            return logging.INFO


env = __OndselEnv()


def joinPath(first, second):
    return os.path.join(first, second).replace("\\", "/")
    # return os.path.normpath(os.path.join(first, second))


def get_extension(name_file):
    ext = os.path.splitext(name_file)[1]
    if ext:
        if ext[0] == ".":
            ext = ext[1:]
    return ext


def isOpenableByFreeCAD(filename):
    "check if FreeCAD can handle this file type"

    if os.path.isdir(filename):
        return False
    if os.path.basename(filename)[0] == ".":
        return False
    extensions = [key.lower() for key in FreeCAD.getImportType().keys()]
    return get_extension(filename).lower() in extensions


def is_freecad_document(name_file):
    return get_extension(name_file).lower() == "fcstd"


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

                return pixmap.scaled(
                    SIZE_PIXMAP, SIZE_PIXMAP, Qt.AspectRatioMode.KeepAspectRatio
                )

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
    logger.setLevel(env.get_debug_level())
    handler = FreeCADHandler()
    if env.get_debug_level() >= logging.INFO:
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


def get_dir_mod():
    return os.path.dirname(os.path.abspath(__file__))


def get_param_group():
    return FreeCAD.ParamGet(PARAM_GROUP)


# ========================
# Versions
# ========================

REMOTE_PACKAGE_URL = (
    "https://raw.githubusercontent.com/Ondsel-Development/"
    "Ondsel-Lens/master/package.xml"
)


def get_addon_version():
    current_dir = get_dir_mod()
    package_xml_file = "package.xml"
    path_package_file = os.path.join(current_dir, package_xml_file)

    with open(path_package_file, "r") as file:
        package_xml_content = file.read()

    return re.search(r"<version>(.*?)<\/version>", package_xml_content).group(1)


def get_server_package_file():
    response = requests.get(REMOTE_PACKAGE_URL, timeout=5)
    if response.status_code == 200:
        return response.text
    return None


def get_local_package_file():
    try:
        with open(local_package_path, "r") as file_:
            return file_.read()
    except FileNotFoundError:
        pass
    return None


def get_version_from_package_file(packageFileStr):
    if packageFileStr is None:
        return None
    lines = packageFileStr.split("\n")
    for line in lines:
        if "<version>" in line:
            version = line.strip().lstrip("<version>").rstrip("</version>")
            return version


def get_latest_version_ondsel_es():
    # raises a RequestException
    response = requests.get(
        "https://api.github.com/repos/Ondsel-Development/FreeCAD/releases/latest"
    )

    if response.status_code == requests.codes.ok:
        json = response.json()
        return json.get("tag_name")

    return None


def get_freecad_version_number():
    version = FreeCAD.Version()
    return f"{version[0]}.{version[1]}.{version[2]}"


def get_current_version_number_ondsel_es():
    if get_source_api_request() == "ondseles":
        return get_freecad_version_number()

    return None


def get_current_version_freecad():
    version = FreeCAD.Version()

    return ", ".join([get_freecad_version_number()] + version[3:])


def get_source_api_request():
    vendor = FreeCAD.ConfigGet("ExeVendor")
    if vendor == "Ondsel":
        return "ondseles"
    elif vendor == "FreeCAD":
        return "freecad"
    else:
        return "unknown"


def get_version_source_api_request():
    return get_current_version_freecad() + ", addon: " + get_addon_version()


def to_version_number(version):
    return [int(n) for n in version.split(".")]


def get_current_revision_freecad():
    return int(FreeCAD.Version()[3][:5])


def version_greater_than(latestVersion, currentVersion):
    latestV = to_version_number(latestVersion)
    currentV = to_version_number(currentVersion)
    if len(latestV) != len(currentV):
        return False  # don't report

    for i in range(len(latestV)):
        if latestV[i] > currentV[i]:
            return True
        elif latestV[i] < currentV[i]:
            return False
        else:
            # these version numbers are the same, so look at the next
            # version number
            pass

    # All are the same
    return False


def convert_to_class_list(json_list, cls):
    """Converts a list of JSON objects into a list of Class objects"""
    temp = []
    if json_list is None:
        return json_list  # for Optional[list[cls]], leave a None as None
    for data in json_list:
        temp.append(cls(**data))
    return temp


def import_json_forgiving_of_extra_fields(cls, json_data):
    """routine for dataclass that is forgiving of extra fields"""
    return cls(
        **{k: v for k, v in json_data.items() if k in inspect.signature(cls).parameters}
    )


def wrapify(text):
    """insert generic text-wrap (ZERO-WIDTH-SPACE) 200B UTF8 char to help with wrapping long filenames"""

    def is_not_wrappable(rune):
        return not (is_eol_wrappable(rune) or is_start_wrappable(rune))

    def is_eol_wrappable(rune):
        """a wrappable punctuation mark and the mark could be at the end of the current line"""
        return rune in ["_", "/", ",", "-"]

    def is_start_wrappable(rune):
        """a wrappable punctuation mark and the mark could start the beginning of next line"""
        return rune in [".", "("]

    new_text = ""
    prev_rune = "9"  # choose a character that would never trigger a wrapping
    for rune in text:
        if is_eol_wrappable(rune) and is_not_wrappable(prev_rune):
            new_text += rune
            new_text += "\u200B"
        elif prev_rune.islower() and rune.isupper():
            # lowercase to uppercase transition such as aA
            new_text += "\u200B"
            new_text += rune
        elif is_start_wrappable(rune) and is_not_wrappable(prev_rune):
            new_text += "\u200B"
            new_text += rune
        else:
            new_text += rune
        prev_rune = rune
    return new_text


@contextmanager
def wait_cursor():
    try:
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        yield
    finally:
        QApplication.restoreOverrideCursor()


def is_lens_url(url):
    parsed_url_lens = urlparse(env.lens_url)
    parsed_url = urlparse(url)

    return (
        parsed_url.scheme == parsed_url_lens.scheme
        and parsed_url.netloc == parsed_url_lens.netloc
    )


def is_hex_digit(character):
    return character in "0123456789abcdefABCDEF"


def is_share_link(url):
    if not is_lens_url(url):
        return False

    parsed_url = urlparse(url)
    parts_path = parsed_url.path.split("/")
    if len(parts_path) < 3:
        return False

    identifier = parts_path[-1]

    return (
        parts_path[-2] == "share"
        and len(identifier) == 24
        and all(is_hex_digit(c) for c in identifier)
    )
