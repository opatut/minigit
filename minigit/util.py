import re, os, sys, datetime
from hashlib import sha512
from minigit import app

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    return s

def hash_password(s):
    return sha512((s + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()

def generate_authorized_keys():
    keys = PublicKey.query.all()
    content = ""

    for key in keys:
        content += 'command="{0} {1}" {2}'.format(
            os.path.join(app.config["ROOTDIR"], "gitserve.py"),
            key.id,
            key.key) + "\n"

def write(l):
    sys.stderr.write(l + "\n")

def die(message):
    write(message)
    log_access("DENIED - " + message)
    sys.exit(1)

def log_access(message):
    with open("access.log", "a") as f:
        m = str(datetime.datetime.utcnow())
        m += " - "
        m += os.getenv("SSH_CLIENT").split()[0]
        m += " - "
        m += message + "\n"
        f.write(m)

def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"

