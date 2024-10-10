# Mock Development Environment

While it is technically possible to run a debugger withing the context of a running instance of FreeCAD/OndselES; thus accessing the debugger, seeing the runtime libs, and getting an IDE to honor all this. It is royal pain in rear to do so.

This is a "mock" environment that makes things easier without bothering with FreeCAD itself.

HOWEVER, it is JUST a mocking environment. Final testing should always be done with FreeCAD and/or OndselES.

## SETUP
 
 - Create a symbolic link in this repo from where-ever you have FreeCAD/OndselES installed for the `PySide` translation. If you are running an AppImage, you will need to explode it. For example:
    
   ```
   ln -s /home/user/Software/Ondsel/OndselES/usr/Ext/PySide PySide
   ```

   The `.gitignore` ignores this out-of-place PySide directory when inside this repo.

 - In a similar manner create a softlink from your local FreeCAD repo's 'requirements.txt' to a 'fc_requirements.txt' in the mock directory.
   
   ```
   ln -s /repos/FreeCAD/requirements.txt /repos/Ondsel-Lens/_mock_environment/fc_requirements.txt
   ```

   Alternatively, you could just copy the content of this file from https://github.com/FreeCAD/FreeCAD/blob/main/requirements.txt . Just remember that it will not change automatically as FreeCAD is updated.

   Warning: do not use this file with `pip`. You will want to use `_mock_environment/requirements.txt` file instead which references the `fc_requirements.txt` file.

 - Clone the https://github.com/obelisk79/OpenTheme repo (if you haven't already). Compile the `.qss` files. Create a softlink to the OpenDark in the `_mock_environment` directory and name it `theme`.

   ```
   ln /repos/OpenTheme/OpenDark -s _mock_environment/theme
   ```

## Using Jetbrain's PyCharm On John's PopOS laptop

- Create a configuration of type `Python` that runs `_mock_environment/_mock_freecad.py` as it's "script" target.
- From settings->`Project: Ondsel_Lens_Addon`->`Python Interpreter` choose a "Add interpreter", Use `VirtualEnv`. The `.gitignore` file is setup to ignore the `venv` directory. So, I put my `Location` at `/home/johnd/Projects/Ondsel-Lens-Addon/venv`. Choose "Inherit global site-packages"
- From an embedded terminal session (see icon at lower left if IDE). The terminal should show a `(venv)` prefixed to the prompt. Run `pip install -r _mock_environment/requirements.txt`



Personally, I used Python 3.11 and had to modify some version numbers. 

In `fc_requirements.txt`, I had to:
 - remove `Pivy` as that comes from my debian package manager not pip,
 - remove the version information from 'PySide2'
 - changed to `ifcopenshell==0.7.10` for mathutils to properly compile.
