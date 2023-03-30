=================
Scipion installer
=================

**Scipion installer** is a python module to install scipion 3 (already in **alfa**)
and not ready for production.

This installer is python2-python3 compatible and is a very lightweight package.
It will create a **python3** virtual environment (conda or virtualenv) with scipion in it.

The entire collection is licensed under the terms of the GNU Public License,
version 3 (GPLv3).

============
Installation
============

It is a 2 lines' installation: First to install the installer, second to use the installer (to install scipion).

*** Python 3 ***

.. code-block::

    python3 -m pip install scipion-installer
    python3 -m scipioninstaller where-to-install-scipion


*** Python2 *** (You are going to need python3 anyway)

.. code-block::

    python2 -m pip install scipion-installer
    python2 -m scipioninstaller where-to-install-scipion

================
Advanced options
================

.. code-block::

    usage: scipioninstaller [-h] [-conda] [-venv] [-dev] [-noXmipp] [-j J] [-dry]
                          [-httpsClone] [-noAsk] [-n N]
                          path

    positional arguments:
      path         Location where you want scipion to be installed.

    optional arguments:
      -h, --help   show this help message and exit
      -conda       Force conda as environment manager, otherwise will use conda
                   anyway if found in the path, else: virtualenv.
      -venv        Force virtualenv as environment manager, otherwise will use
                   conda if found in the path, otherwise: virtualenv.
      -dev         installs components in devel mode
      -noXmipp     Xmipp is installed in devel mode under xmipp-bundle dir by
                   default. This flag skips the Xmipp installation.
      -j J         Number of processors, Xmipp may take a while...
      -dry         Just shows the commands without running them.
      -httpsClone  Only when -dev is active, makes git clones using https instead
                   of ssh
      -noAsk       try to install scipion ignoring some control questions in that
                   process. You must make sure to write the correct path where
                   Scipion will be installed
      -n N         Name of the virtual environment. By default, if this parameter
                   is not passed, the name will be .scipion3env
      -sciBranch SCIBRANCH  Name of the branch of scipion repos to clone when -dev
                   is passed.
      -xmippBranch XMIPPBRANCH
                   Name of the branch of xmipp repos to clone when -dev
                   is passed.



===================
Bundle installation
===================
Checkout Jesper L. Karlsen's script to make a full installation --> https://github.com/jelka71/scipion_auto_install.git

===============
Troubleshooting
===============
**Problem**

    git@github.com: Permission denied (publickey).
    fatal: Could not read from remote repository.

**Solution**
Add :code:`-httpsClone`

----

**Problem**

pip/pip3 is needed to get the installer. 

**Solution**

For ubuntu/debian you might need root access to run

    sudo apt-get install python-pip

No root access?: You can try `pip install --user scipion-installer` to install it locally

----

**Problem**

Missing dependencies: scipion needs python3-tkinter to work and an existing python3 installation.

**Solution**

For ubuntu/debian you might need root access to run 

    sudo apt-get install python3-tk
    
If *Error: “pkg_resources.DistributionNotFound: The 'zipp>=0.5'* is raised when launching installscipion, try to install zipp by

    pip install zipp
