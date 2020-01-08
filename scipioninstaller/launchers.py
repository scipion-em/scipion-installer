VIRTUAL_ENV_VAR = "VIRTUAL_ENV_VAR"
ACTIVATE_ENV_CMD ="ACTIVATE_ENV_CMD"
LAUNCHER_TEMPLATE='''#!/usr/bin/env python
# Scipion launcher
import os
import sys
from os.path import dirname, abspath, join, basename

# Set SCIPION_HOME to the location of this file
scipionHome = os.environ.get("SCIPION_HOME", dirname(abspath(__file__)))
os.environ["PW_ALT_TESTS_CMD"] = basename(__file__) + " tests"

cmd = ""
# Activate the environment if not active
if not os.environ.get('%(VIRTUAL_ENV_VAR)s'):
    cmd = '%(ACTIVATE_ENV_CMD)s && '

cmd += "scipion %%s" %% " ".join(sys.argv[1:])

# Set SCIPION_HOME
os.environ["SCIPION_HOME"] = scipionHome
os.system(cmd)'''