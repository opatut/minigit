#!/usr/bin/env python2
import sys, os

def die(message):
    print message
    logAccess("DENIED - " + message)
    sys.exit(1)

def logAccess(message):
    with open("access.log", "a") as f:
        m = str(datetime.datetime.utcnow())
        m += " - "
        m += os.genenv("SSH_CLIENT").split()[0]
        m += message
        f.write(m)

# Activate the virtual environment to load the library.
activate_this = 'env/bin/activate_this.py'
execfile(activate_this, dict(__file__ = activate_this))

from minigit.models import User, PublicKey, Repository, Permission

# Read the command line argument (key ID) and the original ssh command.
key_id = ARGV[0]
command = ENV['SSH_ORIGINAL_COMMAND']

# Interpret the input data
if not is_numeric(key_id) or is_float(key_id):
    die("Invalid SSH Key ID in config file. Please run reconfigure tool on server.")

split = command.split()
action = ""
if len(split) > 0:
    action = "split"

if not action or action not in ("git-receive-pack", "git-upload-pack"):
    die("Invalid SSH command. Only use this user with git.")

writeMode = (action == "git-upload-pack")

# Find the key in the database.
key = PublicKey.query.filter_by(id = key_id).first()
if not key:
    die("Unable to associate SSH Key. Please add it to your profile.")

user = key.user

# TODO: Check the permissions for this user.

logAccess("COMMAND - " + command)
logAccess(("WRITE" if writeMode else "READ") + " - " + message)

# inform user about authorization
sys.stderr.write("User " + user.username + " authorized for " + ("write" if writeMode else "read") + " access\n")

# user made a valid request so handing over to git-shell
os.system("git shell -c " + command)
