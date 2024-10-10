import sys
from .MockAddonManager import AddonManager

# replace ourselves (a module) with the Class definition.
# I am utterly shocked that this works
sys.modules[__name__] = AddonManager
