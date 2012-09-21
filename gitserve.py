#!/usr/bin/env python2
import sys, os, datetime
from os.path import *

# Activate the virtual environment to load the library.
activate_this = join(dirname(abspath(__file__)), "env", "bin", "activate_this.py")
execfile(activate_this, dict(__file__ = activate_this))

from minigit import app
from minigit.utils import *
from minigit.models import User, PublicKey, Repository, Permission

# Read the command line argument (key ID) and the original ssh command.
key_id = sys.argv[1]
command = os.getenv("SSH_ORIGINAL_COMMAND")

# Interpret the input data
try:
    int(key_id)
except ValueError:
    die("Invalid SSH Key ID in config file. Please run reconfigure tool on server.")

split = command.split() if command else []
action = ""
repo = ""
if len(split) >= 2:
    action = split[0]
    repo = split[1]

    # cut away quotation marks
    if (repo[0] == "'" and repo[-1] == "'") or (repo[0] == '"' and repo[-1] == '"'):
        repo = repo[1:-1]

    # cut away the ".git" fake-extension
    if repo[-4:] == ".git":
        repo = repo[:-4]

if not action or action not in ("git-receive-pack", "git-upload-pack"):
    die("Invalid SSH command. Only use this user with git.")

writeMode = (action == "git-upload-pack")

# Find the key in the database.
key = PublicKey.query.filter_by(id = key_id).first()
if not key:
    die("Unable to associate SSH Key. Please add it to your profile.")
user = key.user

repository = Repository.query.filter_by(slug = repo).first()
if not repository:
    die("Unable to find repository '" + repo + "'. Create or import it first.")

# TODO: Check the permissions for this user.

log_access(("WRITE" if writeMode else "READ") + " - <" + user.username + "> in <" + repo + ">")

# inform user about authorization
write("User " + user.username + " authorized for " + ("write" if writeMode else "read") + " access")

# user made a valid request so handing over to git-shell
os.system("cd {0} && git shell -c {1}".format(app.config["REPOHOME"], shellquote(command)))
