# Ondsel Lens Addon

This FreeCAD addon provides an easy way to upload designs
to [Lens](https://lens.ondsel.com), a cloud service by Ondsel, designed
to publicly share and manipulate FreeCAD projects. The addon is
currently in private beta and requires manual installation.

## Installation

Switch to the location where FreeCAD is installed. 
Change into the Mod directory.

Clone the addon source:

`git clone git@github.com:Ondsel-Development/Ondsel-Lens.git`

or 

`git clone https://github.com/Ondsel-Development/Ondsel-Lens.git`

Start FreeCAD.

You should see the Ondsel Addon shown on the right side of FreeCAD

![image](https://github.com/Ondsel-Development/Ondsel-Lens/assets/538057/4ecccf11-6797-4c81-815e-1fc66db87b08)

## Dependencies

The addon requires a couple of additional Python dependencies that might not
be installed on your machine. Once the addon is available throug the FreeCAD
addon manager, these will be installed automatically.  For now, you may need
to install them manually.

Open the Python console in FreeCAD and enter the following code

```
import addonmanager_dependency_installer
depsInstaller = addonmanager_dependency_installer.DependencyInstaller([],['pyjwt','requests','tzlocal'],[])
depsInstaller._install_python_packages()
```

Note: ```pip install jwt``` installs the wrong library. You need ```pip install pyjwt```.

## First Use (What does the addon do?)

The addon introduces the notion of 'workspaces'. Workspaces are collections
of files that constitute a project. Workspaces are either local or hosted on
the Ondsel Lens server.

### Local workspaces

You may create as many local workspaces as you like.  Each workspace simply
maps to a folder on your hard drive. The workspace will only show the contents
of the folder which are openable by FreeCAD.  Selecting a FreeCAD file will
show additional details including any backup versions in the folder. You can
revert to an earlier version from here if needed.

![image](https://github.com/Ondsel-Development/Ondsel-Lens/assets/538057/57c8942f-6387-4fa2-9ead-4403306b8c6f)

### Ondsel Workspace

An Ondsel workspace works much like a local workspace. To create one, you must
create an account on Ondsel by following the signup link in the dropdown menu.

Once an account is created, you can log in through the addon and enter the
workspace. From here you can save files and access them from another location.

![image](https://github.com/Ondsel-Development/Ondsel-Lens/assets/538057/07d8b957-efe8-4140-a9a5-2a6a3140d507)

### Sharing Links

A file that is hosted on the Ondsel Lens server can be shared and viewed through 
the website. [Sharing links](https://lens.ondsel.com/share/6488bfa93649fe410974f6f9)
can also be fine-tuned to permit the recipient certain privileges including
download formats.

## The state of the Beta

This is an _early_ beta.  We know there are many bugs and missing features. Expect
the UI to change significantly.  This will require you to pull the latest code
from the GitHub repository.  

We are grateful to you for trying the addon and letting us know what you think.
The best place to talk with us about bugs and features is in the Telegram group:
https://t.me/+Q2gm1LdnHotiYWEx.

We've also started a [discussion on GithHub](https://github.com/Ondsel-Development/Ondsel-Lens/discussions/25)
to collect feedback from early adopters.

We have many improvements and additional features planned. We're excited you're here with us!
