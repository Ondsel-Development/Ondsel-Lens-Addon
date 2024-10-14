import tempfile

import FreeCAD

from APIClient import fancy_handle, APICallResult


def download_shared_model_to_memory(api, id_shared_model):
    shared_model = None

    def get_shared_model():
        nonlocal shared_model
        shared_model = api.getSharedModel(id_shared_model)

    api_result = fancy_handle(get_shared_model)
    if api_result == APICallResult.OK:
        pass
    elif api_result == APICallResult.DISCONNECTED:
        return "You must be connected to the Internet to get a file from Ondsel Lens"
    elif api_result == APICallResult.NOT_LOGGED_IN:
        return "You must be logged in to get a file from Ondsel Lens"
    elif api_result == APICallResult.PERMISSION_ISSUE:
        return "You are not allowed to download this particular file from Ondsel Lens"
    else:
        return f"General error found attempting to download file. See Report View tab."
    if not shared_model:
        return f"Unable to locate share link ${id_shared_model}"
    if not shared_model["canDownloadDefaultModel"]:
        return "This share link does not permit downloads of the original file"
    model = shared_model["model"]
    file = model["file"]
    real_filename = file["custFileName"]
    version_id = str(file["currentVersionId"])
    versions = file["versions"]
    unique_filename = [
        ver["uniqueFileName"] for ver in versions if str(ver["_id"]) == version_id
    ][0]
    download_to_memory(api, unique_filename, real_filename)
    return f"Done downloading file '{real_filename}'"


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

    api_result = fancy_handle(get_file_detail)
    if api_result == APICallResult.OK:
        pass
    elif api_result == APICallResult.DISCONNECTED:
        return "You must be connected to the Internet to get a file from Ondsel Lens"
    elif api_result == APICallResult.NOT_LOGGED_IN:
        return "You must be logged in to get a file from Ondsel Lens"
    elif api_result == APICallResult.NOT_LOGGED_IN:
        return "You must be logged in to get a file from Ondsel Lens"
    elif api_result == APICallResult.PERMISSION_ISSUE:
        return "You are not allowed to download this particular file from Ondsel Lens"
    else:
        return f"General error found attempting to download file. See Report View tab."
    download_to_memory(api, unique_filename, real_filename)
    return f"Done downloading file '{real_filename}'"


def download_to_memory(api, unique_filename, real_filename):
    with tempfile.NamedTemporaryFile(prefix="sl_", suffix=".FCStd") as tf:
        api.downloadFileFromServerUsingHandle(unique_filename, tf)
        tf.flush()
        FreeCAD.openDocument(tf.name)
    FreeCAD.ActiveDocument.Label = real_filename
    FreeCAD.ActiveDocument.FileName = ""
