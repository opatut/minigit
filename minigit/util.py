import re, os, sys, datetime, subprocess, iso8601, pytz
from hashlib import sha512
from minigit import app
from os.path import *
from flask import abort

def run(p):
    print("$ " + p)
    return subprocess.check_output(p, shell = True)

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    return s

def get_repo(s, error = 404):
    from minigit.models import Repository
    r = Repository.query.filter_by(slug = s).first()
    if not r and error:
        abort(404)
    return r

def get_email_user(email):
    if not email: return None
    from minigit.models import Email
    m = Email.query.filter_by(address = email).first()
    if not m: return None
    return m.user

def extract_email(git_user):
    a = re.search("<(.*)>", git_user)
    if a:
        return a.group(1)
    return ""

def parse_date(s):
    # Parse timezone offset
    stamp, tz = s.split()
    timezone = iso8601.iso8601.parse_timezone(tz[:3] + ':' + tz[3:])
    return datetime.datetime.fromtimestamp(int(stamp), timezone).astimezone(pytz.utc).replace(tzinfo = None)

def hash_password(s):
    return sha512((s + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()

def generate_authorized_keys():
    from minigit.models import PublicKey
    keys = PublicKey.query.all()
    content = ""

    for key in keys:
        content += 'command="{0} {1}" {2}'.format(
            abspath(join(app.config["ROOTDIR"], "gitserve.py")),
            key.id,
            key.key) + "\n"

    # write authorized keys file
    with open(app.config["AUTHORIZED_KEYS"], 'w') as f:
        f.write(content)

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

