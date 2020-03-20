=================
Scipion installer
=================

**Scipion installer** is a Python module to install scipion 3. Is already in alfa. So not ready
for production.


The entire collection is licensed under the terms of the GNU Public License,
version 3 (GPLv3).

=====
Usage
=====
    pip install scipion-installer

    installscipion <path where you want scipion> -dev -dry [-httpsClone]

    remove -dry, once you understand what it will do.

    pass -httpsClone only if -dev is passed to git clone development repos using https instead os ssh
    
===============
Troubleshooting
===============

Pip is needed to get the installer. For ubuntu/debian you might need root access to run 

    sudo apt-get install python-pip

No root access?: You can try *pip install --user scipion-installer* to install it localy

Missing dependencies: scipion needs python3-tkinter to work and an existing python3 installation.
For ubuntu/debian you might need root access to run 

    sudo apt-get install python3-tk
    
If *Error: “pkg_resources.DistributionNotFound: The 'zipp>=0.5'* is raised when launching installscipion, try to install zipp by

    pip install zipp
