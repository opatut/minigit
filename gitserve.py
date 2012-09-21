#!/usr/bin/env python2
import sys, os, datetime

def write(l):
    sys.stderr.write(l + "\n")

def die(message):
    write(message)
    logAccess("DENIED - " + message)
    sys.exit(1)

def logAccess(message):
    with open("access.log", "a") as f:
        m = str(datetime.datetime.utcnow())
        m += " - "
        m += os.getenv("SSH_CLIENT").split()[0]
        m += " - "
        m += message + "\n"
        f.write(m)

def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"

# Activate the virtual environment to load the library.
current_dir = os.path.dirname(os.path.abspath(__file__))
activate_this = os.path.join(current_dir, "env", "bin", "activate_this.py")
execfile(activate_this, dict(__file__ = activate_this))

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

logAccess(("WRITE" if writeMode else "READ") + " - <" + user.username + "> in <" + repo + ">")

# inform user about authorization
write("User " + user.username + " authorized for " + ("write" if writeMode else "read") + " access")

# user made a valid request so handing over to git-shell
os.system("git shell -c " + shellquote(command))

