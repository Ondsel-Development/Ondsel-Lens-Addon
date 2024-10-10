import sys
from .MockPart import Part
from .MockShape import Shape

# replace ourselves (a module) with the Class definition.
# I am utterly shocked that this works
sys.modules[__name__] = Part
