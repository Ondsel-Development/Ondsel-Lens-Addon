# SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>
#
# SPDX-License-Identifier: LGPL-2.0-or-later

import tempfile

import FreeCAD

from APIClient import fancy_handle, APICallResult

import Utils


logger = Utils.getLogger(__name__)


class HandlerException(Exception):
    pass


def download_shared_model_to_memory(api, id_shared_model):
    shared_model = None

    def get_shared_model():
        nonlocal shared_model
        shared_model = api.getSharedModel(id_shared_model)

    do_api_call(get_shared_model)

    if not shared_model:
        raise HandlerException(f"Unable to locate share link ${id_shared_model}")
    if not shared_model["canDownloadDefaultModel"]:
        raise HandlerException(
            "This share link does not permit downloads of the original file"
        )
    model = shared_model["model"]
    file = model["file"]
    real_filename = file["custFileName"]
    version_id = str(file["currentVersionId"])
    versions = file["versions"]
    unique_filename = [
        ver["uniqueFileName"] for ver in versions if str(ver["_id"]) == version_id
    ][0]
    return download_to_memory(api, unique_filename, real_filename)


def do_api_call(func):
    api_result = fancy_handle(func)
    if api_result == APICallResult.OK:
        pass
    elif api_result == APICallResult.DISCONNECTED:
        raise HandlerException(
            "You must be connected to the Internet to get a file from Ondsel Lens"
        )
    elif api_result == APICallResult.NOT_LOGGED_IN:
        raise HandlerException("You must be logged in to get a file from Ondsel Lens")
    elif api_result == APICallResult.NOT_LOGGED_IN:
        raise HandlerException("You must be logged in to get a file from Ondsel Lens")
    elif api_result == APICallResult.PERMISSION_ISSUE:
        raise HandlerException(
            "You are not allowed to download this particular file from Ondsel Lens"
        )
    else:
        raise HandlerException(
            "General error found attempting to download file. See Report View tab."
        )


def download_file_version_to_memory(api, file_id, version_id, public):
    unique_filename = None
    real_filename = None

    def get_file_detail():
        nonlocal unique_filename, real_filename
        file_detail, version_detail = api.get_file_version_details(
            file_id, version_id, public
        )
        unique_filename = version_detail.uniqueFileName
        real_filename = file_detail.custFileName

    do_api_call(get_file_detail)

    return download_to_memory(api, unique_filename, real_filename)


def download_to_memory(api, unique_filename, real_filename):
    if Utils.isOpenableByFreeCAD(real_filename):
        suffix = "." + Utils.get_extension(real_filename)
        with tempfile.NamedTemporaryFile(prefix="sl_", suffix=suffix) as tf:
            api.downloadFileFromServerUsingHandle(unique_filename, tf)
            tf.flush()
            if Utils.is_freecad_document(real_filename):
                FreeCAD.openDocument(tf.name)
                FreeCAD.ActiveDocument.Label = real_filename
            else:
                FreeCAD.loadFile(tf.name)
            FreeCAD.ActiveDocument.FileName = ""
        return real_filename
    else:
        raise HandlerException(f"FreeCAD cannot open {real_filename}")


def warn_downloaded_file(name_file):
    logger.warn(
        f"Done downloading '{name_file}'. "
        "Be sure to save to disk if you want to keep the model."
    )
