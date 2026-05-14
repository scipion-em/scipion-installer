# -*- coding: utf-8 -*-
import os
import argparse
import sys

from scipioninstaller import INSTALL_ENTRY
# Virtual env programs
from scipioninstaller.launchers import (LAUNCHER_TEMPLATE, VIRTUAL_ENV_VAR,
                                        ACTIVATE_ENV_CMD, PYTHON_PROGRAM)

VENV_ARG = '-venv'
DEFAULT_VALUE_PYTHON_ARG = "3.14"
CMD_SEP = " &&\n"
CONDA = 'conda'
CONDA_ACTIVATION_CMD = "CONDA_ACTIVATION_CMD"
SCIPION_SCRATCH = 'SCIPION_SCRATCH'
SCIPION_ENV = 'scipion3'
LAUNCHER_NAME = "scipion3"


# User answers
YES = "y"
NO = "n"

# Python 2 vs 3 differences
try:  
    # Python 2 methods
    ask = raw_input
except NameError:
    # Python 3 methods
    ask = input


def ask_for_input(message, no_ask):
    if not no_ask:
        return ask(message)
    else:
        print(message, YES)
        return YES


def get_environment_creation_cmd(conda, scipion_home, scipion_env, no_ask, python_version):

    cmd = cmdfy("cd %s" % scipion_home)

    if conda:
        cmd += get_conda_creation_cmd(scipion_env, no_ask, python_version)
    else:
        cmd += get_virtualenv_creation_cmd(scipion_home, scipion_env, python_version)

    return cmd


class InstallationError(Exception):
    pass


def get_conda_creation_cmd(scipion_env, no_ask, python_version):

    cmd = cmdfy(get_conda_init_cmd())

    silent_mode = "-y" if no_ask else ""
    cmd += cmdfy("%s create %s -n %s python=%s pip" % (CONDA, silent_mode, scipion_env, python_version))
    cmd += cmdfy(get_conda_env_activation_cmd(scipion_env))

    return cmd


def get_conda_init_cmd(do_raise=True):

    conda_init = os.environ.get(CONDA_ACTIVATION_CMD, None)

    if conda_init is None:
        return guess_conda_init_cmd(do_raise)
    else:
        return conda_init


def guess_conda_init_cmd(do_raise=True):

    shell = os.path.basename(os.environ.get("SHELL", "bash"))
    conda_path = check_program(CONDA, do_raise)
    if not conda_path:
        return ""
    if shell in ["csh", "tcsh", "zsh"]:
        return '. "%s"' % os.path.join(os.path.dirname(conda_path), "..", "etc",
                                       "profile.d", "conda.sh")
    else:
        return 'eval "$(%s shell.%s hook)"' % (conda_path, shell)


def get_conda_env_activation_cmd(scipion_env):

    return "conda activate %s" % scipion_env


def cmdfy(cmd, sep=CMD_SEP):
    """ Add a command separator like &&\n """
    return cmd + sep


def get_virtualenv_creation_cmd(scipion_home, scipion_env, python_version):

    if python_version == DEFAULT_VALUE_PYTHON_ARG:
        python_version = "python3"

    cmd = cmdfy("%s -m virtualenv --python=%s %s" % (sys.executable, python_version, scipion_env))
    cmd += cmdfy(get_virtualenv_activation_cmd(scipion_home, scipion_env))

    return cmd


def get_virtualenv_activation_cmd(scipion_home, scipion_env):
    return ". %s" % os.path.join(scipion_home, scipion_env, "bin", "activate")


def check_program(program, do_raise=True):
    """Check whether `program` is on PATH.

    :param program: program to check availability for.
    :param do_raise: (True) - raise an exception if not found otherwise, return empty string """

    try:
        from shutil import which

        full_path = which(program)

    # Python 2 case:
    except ImportError:
        from distutils.spawn import find_executable
        full_path = find_executable(program)

    if full_path is None:
        if do_raise:
            raise InstallationError("%s command not found." % program)
        else:
            return ""
    else:
        return full_path


def solve_folder(folder, dry):
    # Check folder exists
    if not os.path.exists(folder):

        try:
            if not dry:
                os.makedirs(folder)
            else:
                print("%s would have been created." % folder)

        except OSError as e:
            print(e)
            raise InstallationError("Please, verify that you have "
                                    "permissions to create %s" % folder)


def get_scipion_installation_cmd(scipion_home):

    cmd = cmdfy("mkdir -p software/lib")
    cmd += cmdfy("mkdir -p software/bindings")
    cmd += cmdfy("mkdir -p software/em")
    cmd += cmdfy("export SCIPION_HOME=%s" % scipion_home)
    cmd += cmdfy("pip install scipion-pyworkflow")
    cmd += cmdfy("pip install scipion-app")

    return cmd


def create_launcher(scipion_home, conda, dry, scipion_env):

    content = LAUNCHER_TEMPLATE
    python_program = os.path.basename(sys.executable)

    conda_init = get_conda_init_cmd(do_raise=False)

    if conda:
        replace_dict = {VIRTUAL_ENV_VAR: "CONDA_DEFAULT_ENV",
                        ACTIVATE_ENV_CMD: conda_init + " && " + get_conda_env_activation_cmd(scipion_env),
                        PYTHON_PROGRAM: str(python_program)}
    else:
        replace_dict = {VIRTUAL_ENV_VAR: "VIRTUAL_ENV",
                        ACTIVATE_ENV_CMD: get_virtualenv_activation_cmd(scipion_home, scipion_env),
                        PYTHON_PROGRAM: str(python_program)}

    # Replace values
    content = content % replace_dict

    launcher_fn = os.path.join(scipion_home, LAUNCHER_NAME)
    write_file(launcher_fn, content, dry)
    run_cmd("chmod +x %s" % launcher_fn, dry)

    return launcher_fn


def write_file(file, content, dry):
    if dry:
        print("%s would've been created with the following content:" % file)
        print("_" * 40)
        print(content)
        print("_" * 40)
    else:
        fh = open(file, "w")
        fh.write(content)
        fh.close()


def create_config_file(scipion_home, scratch_path, dry):
    """
    Create a minimum config file with CONDA_ACTIVATION_CMD and SCIPION_SCRATCH
    variables
    """
    lines = ''
    conda_init = get_conda_init_cmd(False)
    if conda_init:
        lines += CONDA_ACTIVATION_CMD + ' = ' + conda_init + os.linesep
    if scratch_path is not None:
        lines += SCIPION_SCRATCH + ' = ' + scratch_path + os.linesep
    if lines:
        lines = "[PYWORKFLOW]" + os.linesep + lines
        config_path = os.path.join(scipion_home, 'config')
        config_file_name = 'scipion.conf'
        solve_folder(config_path, dry)
        write_file(os.path.join(config_path, config_file_name), lines, dry)


def main():
    try:
        # Arg parser configuration
        parser = argparse.ArgumentParser(prog=INSTALL_ENTRY,
                                         description="Installs scipion3 in a conda or virtualenv environment.\n"
                                                     "Check all parameters bellow for a custom installation. "
                                                     "If there are issues initializing conda you can set %s variable "
                                                     "and it will be used instead of guessing.\n "
                                                     "Typical values are "
                                                     ". \"/path/to/miniconda3/etc/profile.d/conda.sh\" or "
                                                     "eval \"$(/path/to/miniconda3/bin/conda shell.bash hook)\""
                                                     % CONDA_ACTIVATION_CMD,
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

        parser.add_argument('-dry', help='Just shows the commands without running them.',
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

        parser.add_argument('-scratchPath',
                            help='Path to a folder working at high '
                                 'speed(like SSDs) to be used temporarily '
                                 'during processing.',
                            default=None)

        parser.add_argument('-python',
                            help='Python version to use in the environment. For virtualenv, default value will '
                                 'become "python3", otherwise argument will be literally passed to virtualenv.'
                                 'Default value is %s but up to 3.11 may work as well.' % DEFAULT_VALUE_PYTHON_ARG,
                            default=DEFAULT_VALUE_PYTHON_ARG)

        # Parse and fill args
        args = parser.parse_args()
        scipion_home = os.path.abspath(args.path)

        # Decide on environment manager
        if args.conda:
            conda = args.conda
        elif args.venv:
            conda = False
        else:  # decide, favouring conda
            # If conda is detected
            if check_program(CONDA, do_raise=False):
                print("%s detected. Favouring it. If you want a virtualenv installation "
                      "cancel installation and pass %s ." % (CONDA, VENV_ARG))
                conda = True
            else:
                # Fall back to virtualenv
                conda = False

        no_ask = args.noAsk
        dry = args.dry
        scratch_path = args.scratchPath
        python = args.python

        # Creating the Scratch Folder
        if scratch_path is not None:
            solve_folder(scratch_path, dry)

        # Check Scipion home folder and create it if applies.
        solve_folder(scipion_home, dry)
        scipion_env = args.n
        if not conda and scipion_env == SCIPION_ENV:
            scipion_env = '.' + scipion_env

        cmd = get_environment_creation_cmd(conda, scipion_home, scipion_env, no_ask, python)
        # Creating Scipion installation command and the launcher
        cmd += get_scipion_installation_cmd(scipion_home)
        # Flush stdout
        sys.stdout.flush()
        run_cmd(cmd, dry)
        launcher = create_launcher(scipion_home, conda, dry, scipion_env)
        print("------------------------------------")
        print("Scipion core successfully installed.")
        print("------------------------------------")

        # Creating a minimum Scipion config file
        create_config_file(scipion_home, scratch_path, dry)

        if not dry:
            header = "Installation successfully finished!! Happy EM processing!!"
            content = "You can launch Scipion using the launcher at: %s " % launcher
            create_message_installation(header, [content])

    except InstallationError as e:
        header = "Installation failed"
        content = []
        errors = str(e).split("\n")
        for error in errors:
            content.append(error)
        content.append(" ")
        content.append("For more information about the installation errors that can appear when installing or ")
        content.append("using Scipion go to: https://scipion-em.github.io/docs/docs/user/troubleshooting.html ")
        create_message_installation(header, content)
        sys.exit(-1)
    except KeyboardInterrupt:
        header = "Installation cancelled"
        content = ["The installation has been interrupted, probably by pressing \"Ctrl + c\"."]
        create_message_installation(header, content)
        sys.exit(-1)


def create_message_installation(header="", content=None):
    """
    Create a table related with Scipion installation
    """
    if content is None:
        content = []

    required_width = max([len(c) for c in content])

    print("")

    horizontal_line = "_" * required_width
    start_row = " _" + horizontal_line + " "
    print(start_row)

    # Print the header
    empty_line = "| " + " " * required_width + "|"
    print(empty_line)
    number_of_spaces = required_width - len(header)
    header_content = "| " + header + " " * number_of_spaces + "|"
    print(header_content)

    # Print the content
    end_row = " _" + horizontal_line + " "
    print(end_row)
    print("")
    for line in content:
        line = "  " + line
        print(line)

    print(end_row)


def run_cmd(cmd, dry):
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
