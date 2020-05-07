VIRTUAL_ENV_VAR = "VIRTUAL_ENV_VAR"
ACTIVATE_ENV_CMD ="ACTIVATE_ENV_CMD"
LAUNCHER_TEMPLATE='''#!/usr/bin/env python
# Scipion launcher
import os
import sys
from os.path import dirname, abspath, join, basename

# Set SCIPION_HOME to the location of this file
scipionHome = dirname(abspath(__file__))
os.environ["SCIPION_TESTS_CMD"] = basename(__file__) + " tests"
os.environ["LD_LIBRARY_PATH"] = ":".join([os.environ.get("LD_LIBRARY_PATH", ""), join(scipionHome, "software", "lib")])
os.environ["PYTHONPATH"] = ":".join([os.environ.get("PYTHONPATH", ""), join(scipionHome, "software", "bindings")])

cmd = ""
if len(sys.argv) > 1 and sys.argv[1] == 'git':
    for repo in ['scipion-app', 'scipion-pyworkflow', 'scipion-em']:
        cmd += ("(cd "+join(scipionHome, repo)+" ; echo ' > in "+repo+":' ;"
                " git "+' '.join(sys.argv[2:])+" ; echo) ; ")
else:
    # Activate the environment
    cmd = '%(ACTIVATE_ENV_CMD)s && '
    cmd += "python -m scipion %%s" %% " ".join(sys.argv[1:])

# Set SCIPION_HOME
os.environ["SCIPION_HOME"] = scipionHome
exit(os.WEXITSTATUS(os.system(cmd)))'''