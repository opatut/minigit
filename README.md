# Minigit - Git permissions and Web frontend

## What it does

The application has two main uses:

1) Display repository information / files in a web browser.

2) Control permissions from the web frontend and apply them to git pull / push calls.

## How it works

The webapp displays data parsed from the git object files in the bare server repository.The users from the commits are associated with database users based on their eMail address.

For read/write permission control, the webapp writes a `command=gitserve.py $KEY_ID` option into the authorized\_keys file. The `gitserve.py` script can read out the user associated with the public key and redirect the git-receive-pack/git-upload-pack commands or reject them, based on the user's permissions for the requested repository found in the database.

**DO NOT EDIT THE AUTHORIZED_KEYS FILE MANUALLY**. The webapp will overwrite any changes anyway. The `gituser` will not be used for login, only for use with the webapp.

Git remote URLs will have this pattern:

    git://${gituser}@${yourserver}:${sshport}/${repo-slug}.git

## How to use it

This application requires:

* python-virtualenv
* git

When you run the webapp for the first time, run the setup script `setup.sh` to create the virtual environment and install all other requirements into it. The virtual environment is necessary to not clutter your system with the python packages and keep their versions independent from your system versions.

You will also create a configuration file `config.py` from the example file provided. To initialize the database, activate the virtual environment (see below) and run the `kill-database.py` script.

Then, to run the test server, activate the virtual environment and run the server script:

    source env/bin/activate
    ./run.py

You need to have write permission to the repository directory and the authorized\_keys file.

