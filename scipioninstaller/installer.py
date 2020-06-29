# !/usr/bin/env python
import os
import argparse
import sys

from scipioninstaller import INSTALL_ENTRY
# Virtual env programs
from scipioninstaller.launchers import (LAUNCHER_TEMPLATE, VIRTUAL_ENV_VAR,
                                        ACTIVATE_ENV_CMD)

VENV_ARG = '-venv'

CMD_SEP = " &&\n"
CONDA = 'conda'
SCIPION_ENV = '.scipion3env'
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
    cmd += cmdfy("%s create %s -n %s python=3" % (CONDA, silentMode, scipionEnv))
    cmd += cmdfy(getCondaenvActivationCmd(scipionEnv))
    return cmd

def getCondaInitCmd():
    shell = os.path.basename(os.environ.get("SHELL"))
    return 'eval "$(%s shell.%s hook)"' % (checkProgram(CONDA), shell)


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


def checkProgram(program):
    """Check whether `name` is on PATH."""

    from distutils.spawn import find_executable

    fullPath = find_executable(program)

    if fullPath is None:
        raise InstallationError("%s command not found." % program)
    else:
        return fullPath

def solveScipionHome(scipionHome, dry, noAsk):
    # Check folder exists
    if not os.path.exists(scipionHome):

        answer = askForInput("path %s does not exists. Shall I create "
                             "it? (%s/%s): " % (scipionHome, YES, NO), noAsk)

        if answer != YES:
            raise InstallationError("Cannot continue without creating %s" %
                                    scipionHome)
        else:
            try:
                if not dry:
                    os.mkdir(scipionHome)
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
    
    if not os.path.exists(os.path.join(scipionHome,
                                       repoName if cloneFolder == '' else cloneFolder)):
        cmd = cmdfy("git clone --branch %s %s %s" % (branch, cloneUrl,
                                                     cloneFolder))
    else:
        cmd = ""
        print("Print %s repository detected, skipping clone." % repoName)

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
            cmd += cmdfy("xmipp-bundle/xmipp config")  # This reset the xmipp.conf
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

    if conda:
        replaceDict = {VIRTUAL_ENV_VAR: "CONDA_DEFAULT_ENV",
                        ACTIVATE_ENV_CMD: getCondaInitCmd() + " && " + getCondaenvActivationCmd(scipionEnv)}
    else:
        replaceDict = {VIRTUAL_ENV_VAR: "VIRTUAL_ENV",
                        ACTIVATE_ENV_CMD: getVirtualenvActivationCmd(scipionHome, scipionEnv)}

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
        parser = argparse.ArgumentParser(prog=INSTALL_ENTRY, epilog="Happy Scipioning!")
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
            if checkProgram(CONDA):
                print("% detected. Favouring it. If you want a virtualenv installation "
                      "cancel installation and pass %s it." % (CONDA, VENV_ARG))
                conda = True
            else:
                # Fall back to virtualenv
                conda = False

        noAsk = args.noAsk


         # Warn about conda fonts...
        if conda and askForInput("Conda installations will have a poor font and may"
            " affect your user experience. Are you sure you want to continue? (%s/%s): " % (YES, NO), noAsk) !=YES:
            raise InstallationError("Cancelling installation with conda.")

        dev = args.dev

        if askForInput("This is an early version of the installer. "
                       "So far only works for developers installing an unstable version."
                       "Are you sure you want to continue? (%s/%s): " % (
                                 YES, NO), noAsk) != YES:
            raise InstallationError("User cancelled development/unstable installation.")

        dry = args.dry
        checkProgram(GIT) if dev else None
        # Check Scipion home folder and create it if apply.
        solveScipionHome(scipionHome, dry, noAsk)
        scipionEnv = args.n

        cmd = getEnvironmentCreationCmd(conda, scipionHome, scipionEnv, noAsk)
        cmd += getInstallationCmd(scipionHome, dev, args)
        runCmd(cmd, dry)

        launcher = createLauncher(scipionHome, conda, dry, scipionEnv, dev)
        if not dry:
            print("\n\nScipion has been successfully installed!! Happy EM processing!!\n\n")
            print("You can launch Scipion using the launcher at %s\n" % launcher )

    except InstallationError as e:
        print(str(e))
        print("Installation cancelled.")
    except KeyboardInterrupt as e:
        print("\nInstallation cancelled, probably by pressing \"Ctrl + c\".")


def runCmd(cmd, dry):

    # remove last CMD_SEP
    if cmd.endswith(CMD_SEP):
        cmd = cmd[:-len(CMD_SEP)]

    if dry:
        print(cmd)
    else:
        val = os.system(cmd)
        if val != 0:
            raise InstallationError("Something went wrong running: \n %s" % cmd)


if __name__ == '__main__':
    main()


