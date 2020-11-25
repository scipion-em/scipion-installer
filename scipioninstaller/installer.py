# -*- coding: utf-8 -*-
import os
import argparse
import sys

from scipioninstaller import INSTALL_ENTRY
# Virtual env programs
from scipioninstaller.launchers import (LAUNCHER_TEMPLATE, VIRTUAL_ENV_VAR,
                                        ACTIVATE_ENV_CMD, PYTHON_PROGRAM, CONDA_ACTIVATION_LINE)

VENV_ARG = '-venv'

CMD_SEP = " &&\n"
CONDA = 'conda'
CONDA_ACTIVATION_CMD = "CONDA_ACTIVATION_CMD"
SCIPION_ENV = 'scipion3'
GIT = 'git'
LAUNCHER_NAME = "scipion3"

XMIPP_DEFAULT_BRANCH = "devel"
SCIPION_DEFAULT_BRANCH = "devel"
# User answers
YES = "y"
NO = "n"

# Python 2 vs 3 differences
try:  
    # Python 2 methods
    ask = raw_input
except:
    # Python 3 methods
    ask = input


def askForInput(message, noAsk):
    if not noAsk:
        return ask(message)
    else:
        print(message, YES)
        return YES


def getEnvironmentCreationCmd(conda, scipionHome, scipionEnv, noAsk):
    if conda:
        cmd = getCondaCmd(scipionEnv, noAsk)
    else:
        cmd = getVirtualenvCmd(scipionHome, scipionEnv)

    return cmd


class InstallationError(Exception):
    pass


def getCondaCmd(scipionEnv, noAsk):

    silentMode = "-y" if noAsk else ""
    cmd = cmdfy(getCondaInitCmd())
    cmd += cmdfy("%s create %s -n %s python=3.8" % (CONDA, silentMode, scipionEnv))
    cmd += cmdfy(getCondaenvActivationCmd(scipionEnv))
    return cmd


def getCondaInitCmd(doRaise=True):

    conda_init = os.environ.get(CONDA_ACTIVATION_CMD, None)

    if conda_init is None:
        return guessCondaInitCmd(doRaise)
    else:
        return conda_init

def guessCondaInitCmd(doRaise=True):

    shell = os.path.basename(os.environ.get("SHELL", "bash"))
    condaPath = checkProgram(CONDA, doRaise)
    if not condaPath:
        return ""
    if shell in ["csh", "tcsh", "zsh"]:
        return '. "%s"' % os.path.join(os.path.dirname(condaPath), "..", "etc",
                                       "profile.d", "conda.sh")
    else:
        return 'eval "$(%s shell.%s hook)"' % (condaPath, shell)


def getCondaenvActivationCmd(scipionEnv):

    return "conda activate %s" % scipionEnv


def cmdfy(cmd, sep=CMD_SEP):
    """ Add a command separator like &&\n """
    return cmd + sep


def getVirtualenvCmd(scipionHome, scipionEnv):

    cmd = cmdfy("cd %s" % scipionHome)
    cmd += cmdfy("%s -m virtualenv --python=python3 %s" % (sys.executable,
                                                           scipionEnv))
    cmd += cmdfy(getVirtualenvActivationCmd(scipionHome, scipionEnv))
    return cmd


def getVirtualenvActivationCmd(scipionHome, scipionEnv):
    return ". %s" % os.path.join(scipionHome, scipionEnv, "bin", "activate")


def checkProgram(program, doRaise=True):
    """Check whether `name` is on PATH.
    :param doRaise: (True) - raise an exception if not found otherwise, return empty string """

    from distutils.spawn import find_executable

    fullPath = find_executable(program)

    if fullPath is None:
        if doRaise:
            raise InstallationError("%s command not found." % program)
        else:
            return ""
    else:
        return fullPath

def solveScipionHome(scipionHome, dry):
    # Check folder exists
    if not os.path.exists(scipionHome):

        try:
            if not dry:
                os.makedirs(scipionHome)
            else:
                print ("%s would have been created." % scipionHome)

        except OSError as e:
            print (e)
            raise InstallationError("Please, verify that you have "
                                    "permissions to create %s" % scipionHome)


def getRepoInstallCommand(scipionHome, repoName, useHttps,
                          organization='scipion-em', branch='devel',
                          pipInstall=True, cloneFolder=''):
    
    # Choose url type: ssh or https
    cloneUrl= 'git@github.com:%s/%s.git' if not useHttps else 'https://github.com/%s/%s.git'

    # replace the repository name
    cloneUrl = cloneUrl % (organization, repoName)
    folderName = repoName if cloneFolder == '' else cloneFolder

    if not os.path.exists(os.path.join(scipionHome, folderName)):
        cmd = cmdfy("git clone --branch %s %s %s" % (branch, cloneUrl,
                                                     cloneFolder))
    else:
        print("%s repository detected, it will be updated." % folderName)
        cmd = cmdfy("cd %s" % folderName)
        cmd += cmdfy("git pull")
        cmd += cmdfy("cd ..")

    if pipInstall:
        cmd += cmdfy("pip install -e %s" % repoName)

    return cmd


def getInstallationCmd(scipionHome, dev, args):

    cmd = cmdfy("cd %s" % scipionHome)
    cmd += cmdfy("mkdir -p software/lib")
    cmd += cmdfy("mkdir -p software/bindings")
    cmd += cmdfy("mkdir -p software/em")
    cmd += cmdfy("export SCIPION_HOME=%s" % scipionHome)

    noXmipp = args.noXmipp

    if dev:
        useHttps = args.httpsClone

        # Scipion repos
        cmd += getRepoInstallCommand(scipionHome, "scipion-pyworkflow", useHttps, branch=args.sciBranch)
        cmd += getRepoInstallCommand(scipionHome, "scipion-em", useHttps, branch=args.sciBranch)
        cmd += getRepoInstallCommand(scipionHome, "scipion-app", useHttps, branch=args.sciBranch)

        if not noXmipp:
            #Xmipp repos
            cmd += cmdfy("echo '\033[1m\033[95m > Installing Xmipp-dev ...\033[0m'")
            cmd += getRepoInstallCommand(scipionHome, "xmipp", useHttps,
                                         organization='i2pc', branch=args.xmippBranch,
                                         pipInstall=False, cloneFolder='xmipp-bundle')
            cmd += cmdfy("xmipp-bundle/xmipp get_devel_sources %s" % args.xmippBranch)
            cmd += cmdfy("xmipp-bundle/xmipp config %s" % ('noAsk' if args.noAsk else ''))  # This reset the xmipp.conf
            cmd += cmdfy("pip install -e xmipp-bundle/src/scipion-em-xmipp")
            cmd += cmdfy("python -m scipion installb xmippDev -j %s" % args.j)

    else:
        cmd += cmdfy("pip install scipion-pyworkflow")
        cmd += cmdfy("pip install scipion-app")

        if not noXmipp:
            cmd += cmdfy("python -m scipion installp -p scipion-em-xmipp -j %s" % args.j)
    return cmd


def createLauncher(scipionHome, conda, dry, scipionEnv, devel=False):

    if devel:
        # TODO: Contemplate different launcher template (ex: scipion3 git [options])
        content = LAUNCHER_TEMPLATE
    else:
        content = LAUNCHER_TEMPLATE

    pythonProgram = os.path.basename(sys.executable)

    condaInit = getCondaInitCmd(doRaise=False)

    if conda:
        replaceDict = {VIRTUAL_ENV_VAR: "CONDA_DEFAULT_ENV",
                       ACTIVATE_ENV_CMD: condaInit + " && " + getCondaenvActivationCmd(scipionEnv),
                       PYTHON_PROGRAM: str(pythonProgram)}
    else:
        replaceDict = {VIRTUAL_ENV_VAR: "VIRTUAL_ENV",
                       ACTIVATE_ENV_CMD: getVirtualenvActivationCmd(scipionHome, scipionEnv),
                       PYTHON_PROGRAM: str(pythonProgram)}

    # Add CONDA_ACTIVATION_CMD variable if possible
    if condaInit:
        replaceDict[CONDA_ACTIVATION_LINE] = "os.environ['CONDA_ACTIVATION_CMD'] = '%s'" % condaInit
    else:
        replaceDict[CONDA_ACTIVATION_LINE] = ""

    # Replace values
    content = content % replaceDict

    launcherFn = os.path.join(scipionHome, LAUNCHER_NAME)
    if dry:
        print("A python executable script would've been created at %s with the following content:" % launcherFn)
        print("_" * 40)
        print(content)
        print("_" * 40)
    else:
        fh = open(launcherFn, "w")
        fh.write(content)
        fh.close()

    runCmd("chmod +x %s" % launcherFn, dry)

    return launcherFn


def main():
    try:
        # Arg parser configuration
        parser = argparse.ArgumentParser(prog=INSTALL_ENTRY,
                                         description= "Installs scipion3 in a conda or virtualenv environment.\n"
                                                      "Check all parameters bellow for a custom installation. If there are issues initializing "
                                                      " conda you can set %s variable and it will be used instead of guessing.\n "
                                                      "Typical values are . \"/path/to/miniconda3/etc/profile.d/conda.sh\" or "
                                                      "eval \"$(/path/to/miniconda3/bin/conda shell.bash hook)\"" % CONDA_ACTIVATION_CMD,
                                         epilog="Happy Scipioning!")
        parser.add_argument('path',
                            help='Location where you want scipion to be installed.')
        parser.add_argument('-conda',
                            help='Force conda as environment manager, otherwise will use conda anyway if '
                                 'found in the path, else: virtualenv.',
                            action='store_true')
        parser.add_argument(VENV_ARG,
                            help='Force virtualenv as environment manager, otherwise will use conda if '
                                 'found in the path, otherwise: virtualenv.',
                            action='store_true')

        parser.add_argument('-dev', help='installs components in devel mode',
                            action='store_true')
        parser.add_argument('-noXmipp', help='Xmipp is installed in devel mode '
                                             'under xmipp-bundle dir by default. '
                                             'This flag skips the Xmipp installation.',
                            action='store_true')
        parser.add_argument('-j', help='Number of processors, Xmipp may take a while...',
                            default=8)
        parser.add_argument('-dry', help='Just shows the commands without running them.',
                            action='store_true')
        
        parser.add_argument('-httpsClone', help='Only when -dev is active, '
                                                'makes git clones using https '
                                                'instead of ssh',
                            action='store_true')

        parser.add_argument('-noAsk',
                            help='try to install scipion ignoring some '
                                 'control questions in that process. You must '
                                 'make sure to write the correct path where '
                                 'Scipion will be installed',
                            action='store_true')
        parser.add_argument('-n', help='Name of the virtual environment. '
                                             'By default, if this parameter is '
                                             'not passed, the name will be '
                                             + SCIPION_ENV,
                            default=SCIPION_ENV)

        parser.add_argument('-sciBranch', help='Name of the branch of scipion repos to clone when -dev is passed.',
                            default=SCIPION_DEFAULT_BRANCH)

        parser.add_argument('-xmippBranch', help='Name of the branch of xmipp repos to clone when -dev is passed.',
                            default=XMIPP_DEFAULT_BRANCH)
        # Parse and fill args
        args = parser.parse_args()
        scipionHome = os.path.abspath(args.path)

        # Decide on environment manager
        if args.conda:
            conda = args.conda
        elif args.venv:
            conda = False
        else: # decide, favouring conda
            # If conda is detected
            if checkProgram(CONDA, doRaise=False):
                print("%s detected. Favouring it. If you want a virtualenv installation "
                      "cancel installation and pass %s ." % (CONDA, VENV_ARG))
                conda = True
            else:
                # Fall back to virtualenv
                conda = False

        noAsk = args.noAsk
        dev = args.dev
        dry = args.dry

        checkProgram(GIT) if dev else None
        # Check Scipion home folder and create it if apply.
        solveScipionHome(scipionHome, dry)
        scipionEnv = args.n
        if not conda and scipionEnv == SCIPION_ENV:
            scipionEnv = '.' + scipionEnv

        cmd = getEnvironmentCreationCmd(conda, scipionHome, scipionEnv, noAsk)
        cmd += getInstallationCmd(scipionHome, dev, args)
        # Flush stdout
        sys.stdout.flush()
        runCmd(cmd, dry)

        launcher = createLauncher(scipionHome, conda, dry, scipionEnv, dev)
        if not dry:
            header = "Scipion has been successfully installed!! Happy EM processing!!"
            content = "You can launch Scipion using the launcher at: %s " % launcher
            createMessageInstallation(header, [content])

    except InstallationError as e:
        header = "Installation failed"
        content = []
        errors = str(e).split("\n")
        for error in errors:
            content.append(error)
        content.append(" ")
        content.append("For more information about the installation errors that can appear when installing or ")
        content.append("using Scipion go to: https://scipion-em.github.io/docs/docs/user/troubleshooting.html ")
        createMessageInstallation(header, content)
        sys.exit(-1)
    except KeyboardInterrupt as e:
        header = "Installation cancelled"
        content = []
        content.append("The installation has been interrupted, probably by pressing \"Ctrl + c\".")
        createMessageInstallation(header, content)
        sys.exit(-1)


def createMessageInstallation(header="", content=[]):
    """
    Create a table related with Scipion installation
    """
    requiredWidth = max([len(c) for c in content])

    horizontalLine = "_" * requiredWidth

    topTable = " _" + horizontalLine + " "
    emptyLine = "| " + " " * requiredWidth + "|"
    botomTable = " _" + horizontalLine + " "
    divRowTable = botomTable
    print("")
    print(topTable)
    print(emptyLine)
    numberOfSpaces = requiredWidth - len(header)
    headerContent = "| " + header + " " * numberOfSpaces  + "|"
    print(headerContent)
    print(divRowTable)
    print("")
    for line in content:
        numberOfSpaces = requiredWidth - len(line)
        lineContend = "  " + line
        print(lineContend)
    print(botomTable)


def runCmd(cmd, dry):
    # remove last CMD_SEP
    if cmd.endswith(CMD_SEP):
        cmd = cmd[:-len(CMD_SEP)]

    if dry:
        print(cmd)
    else:
        val = os.system(cmd)
        if val != 0:
            raise InstallationError("Something went wrong (SEE ERRORS ABOVE) when running: \n\n %s" % cmd)


if __name__ == '__main__':
    main()


