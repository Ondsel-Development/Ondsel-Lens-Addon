import os
import sys

import platform

# import winreg as reg

import Utils


logger = Utils.getLogger(__name__)


# ====================================
# Windows
# ====================================


# def register_url_scheme_windows(scheme, path_executable):
#     key = reg.HKEY_CURRENT_USER
#     subkey = f"Software\\Classes\\{scheme}"
#     command = f'"{executable_path}" "%1"'

#     try:
#         reg.CreateKey(key, subkey)
#         reg.SetValue(key, subkey, reg.REG_SZ, f"URL:{scheme} Protocol")
#         reg.SetValueEx(reg.OpenKey(key, subkey), "URL Protocol", 0, reg.REG_SZ, "")
#         reg.CreateKey(key, f"{subkey}\\shell")
#         reg.CreateKey(key, f"{subkey}\\shell\\open")
#         reg.CreateKey(key, f"{subkey}\\shell\\open\\command")
#         reg.SetValue(key, f"{subkey}\\shell\\open\\command", reg.REG_SZ, command)
#         print(f"URL scheme {scheme} registered successfully")
#     except Exception as e:
#         print(f"Failed to register URL scheme: {e}")


# ====================================
# Linux
# ====================================


def get_path_appimage():
    return os.getenv("APPIMAGE")


def is_app_image():
    return get_path_appimage()


def register_url_scheme_linux(scheme, path_executable, path_macro):
    desktop_entry = f"""
[Desktop Entry]
Name=Ondsel Lens URL Handler
Exec={path_executable} --single-instance {path_macro} --pass %u
Type=Application
NoDisplay=true
MimeType=x-scheme-handler/{scheme};
"""

    name_desktop_file = f"{scheme}.desktop"
    path_desktop_file = os.path.expanduser(
        f"~/.local/share/applications/{name_desktop_file}"
    )
    path_mimeapps_list = os.path.expanduser("~/.config/mimeapps.list")

    with open(path_desktop_file, "w") as desktop_file:
        desktop_file.write(desktop_entry)

    already_registered = False
    scheme_entry = f"x-scheme-handler/{scheme}={path_desktop_file}"

    if os.path.exists(path_mimeapps_list):
        with open(path_mimeapps_list, "r") as mimeapps_list:
            for line in mimeapps_list:
                if scheme_entry in line:
                    already_registered = True
                    break

    # If not already registered, add the new entry
    if not already_registered:
        with open(path_mimeapps_list, "a") as mimeapps_list:
            mimeapps_list.write(f"{scheme_entry}\n")

    os.system(f"xdg-mime default {name_desktop_file} x-scheme-handler/{scheme}")


def get_path_macro():
    return Utils.joinPath(Utils.get_dir_mod(), "lens_handler.FCMacro")


def register_lens_handler():
    name_os = platform.system()
    if name_os == "Linux":
        path_executable = get_path_appimage() if is_app_image() else sys.argv[0]
        abs_path_executable = os.path.abspath(path_executable)
        register_url_scheme_linux(
            Utils.URL_SCHEME, abs_path_executable, get_path_macro()
        )
    else:
        logger.warn(f"Cannot install handler on {platform}")
