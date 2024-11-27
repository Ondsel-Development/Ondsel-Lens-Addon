<!--
SPDX-FileCopyrightText: 2024 Ondsel <development@ondsel.com>

SPDX-License-Identifier: LGPL-2.0-or-later
-->

# Ondsel Lens Addon

This FreeCAD addon provides a convenient way to upload designs
to [Lens](https://lens.ondsel.com), a cloud service by Ondsel, designed
to publicly share and manipulate FreeCAD projects.

## Installation

The Ondsel Lens addon is already installed by default in [Ondsel ES](https://ondsel.com/download/).
For FreeCAD, the Ondsel Lens addon is available through the FreeCAD Addon Manager.

Open the Addon manager. Find in the list 'Ondsel-Lens' and install it.
The installation will require restarting FreeCAD.

You should see the Ondsel Addon in its own tab besides Start.  If it doesn't appear, you can click the yellow or orange Ondsel button or you can type Ctrl-L.

<!-- ![image](https://github.com/Ondsel-Development/Ondsel-Lens/assets/538057/766b7cd7-5c0a-409b-9135-940be8b2fe54)-->
![image](https://github.com/user-attachments/assets/7cc30135-4b7f-4bc3-9cfc-d7ce78621ba6)

## Dependencies

The addon requires a couple of additional Python dependencies that should be installed automatically by the FreeCAD addon manager.

If you have a problem with dependencies you can install them manually by:
Open the Python console in FreeCAD and enter the following code

```
import addonmanager_dependency_installer
depsInstaller = addonmanager_dependency_installer.DependencyInstaller([],['pyjwt','requests','tzlocal'],[])
depsInstaller._install_python_packages()
```

Note: ```pip install jwt``` installs the wrong library. You need ```pip install pyjwt```.

## First Use (What does the addon do?)

The addon introduces the notion of "workspaces". Workspaces are collections of
files that constitute a project and are hosted on the Ondsel Lens server.  To
start working and collaborating on FreeCAD designs, you must create an account
on Ondsel Lens by following the signup link in the dropdown menu.

Once an account is created, you can log in through the addon and enter your
workspace "Default (Personal)".  From here you can save files and access them
from another location.

In addition, you can browse examples curated by Ondsel (the Ondsel Start tab),
browse your bookmarks, search for models, or view the most recent models that are shared on Lens.

<!-- needs to be updated with images from the new flavor -->
<!-- ![image](https://github.com/Ondsel-Development/Ondsel-Lens/assets/538057/5de4781c-b90c-4de1-bd8a-e23283348fbd) -->
![image](https://github.com/user-attachments/assets/d59fb797-bdc8-44a7-b84c-dcec3a2e30a4)

### Workspaces

A workspace maps to a folder on your hard drive and contains files
and folders.  Files can be in five different states:

- "Untracked": Ondsel Lens does not track this file
- "Not downloaded": The file is only available on Lens
- "Synced": the local version is in sync with the Ondsel Lens version
- "Local copy newer": The local version is newer than the server one
- "Lens copy newer": The server version is newer than the local one

By means of download and upload actions, files can be synchronized with the
Lens service and Lens maintains different versions for files.  One version of
each file is marked as the active version which typically is the last
version of a file.  Uploading a new version makes that version the active one.

The addon shows additional details for FreeCAD files.  It shows a thumbnail
of the file, the version information and share links of the file.

### Sharing Links

A file that is hosted on the Ondsel Lens server can be shared and viewed through 
the website. [Sharing links](https://lens.ondsel.com/share/6488bfa93649fe410974f6f9)
can also be fine-tuned to permit the recipient certain privileges including
download formats.

### Offline workflow

The addon also allows for an offline workflow.  If a user is logged out, it is
still possible to work on the files of workspaces that are currently on disk.
As soon as a user logs into Lens, the user has the ability to upload the new
versions to Lens.

## Contact

We are grateful to you for using the addon and letting us know what you think.
The best place to talk with us about bugs and features is on our [Discord Server](https://discord.gg/7jmzezyyfP)

We have many improvements and additional features planned.  Follow the development on the
[GitHub page](https://github.com/Ondsel-Development/Ondsel-Lens) and feel free to raise issues there.
We're excited you're here with us!
