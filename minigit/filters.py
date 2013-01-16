from minigit import app
from minigit.models import Email
from datetime import *
from dateutil import relativedelta
from flask import Markup
import time, os, pygments, pygments.lexers, pygments.formatters, git, re
from os.path import *

# convert unix timestamp to datetime
@app.template_filter()
def gittime(unix):
    return datetime.fromtimestamp(unix)

# format a timestamp in default format (0000-00-00 00:00:00)
@app.template_filter()
def formattime(s):
    return s.strftime("%Y-%m-%d %H:%M:%S")

@app.template_filter()
def nicedate(s):
    return s.strftime("%B %d, %Y")

@app.template_filter()
def highlightsheet(s):
    return pygments.formatters.HtmlFormatter(style = s).get_style_defs('.highlight')

@app.template_filter()
def highlight(s, filename):
    s = s.strip()
    try:
        lexer = pygments.lexers.get_lexer_for_filename(filename)
    except pygments.util.ClassNotFound:
        lexer = pygments.lexers.TextLexer()
    formatter = pygments.formatters.HtmlFormatter(linenos = True)
    return Markup(pygments.highlight(s, lexer, formatter))

@app.template_filter()
def parentpath(s):
    return normpath(join(s, ".."))

@app.template_filter()
def newlines(s):
    return Markup(s.replace("<", "&lt;").strip("\n").replace("\n", "<br />"))

@app.template_filter()
def filesize(s):
    s = int(s)
    for x in ['B', 'KB','MB','GB','TB']:
        if s < 1024.0:
            return "%3.f %s" % (s, x)
        s /= 1024.0

def _s(n, s):
    if n == 0:
        return ""
    return str(n) + " " + s + ("s" if n > 1 else "")

def _delta(delta):
    short = True
    threshold = 2
    if delta.years > 0:
        return _s(delta.years, "year") + ("" if short or delta.years > threshold else " " + _s(delta.months, "month"))
    if delta.months > 0:
        return _s(delta.months, "month") + ("" if short or delta.months > threshold else " " + _s(delta.days, "day"))
    if delta.days > 0:
        return _s(delta.days, "day") + ("" if short or delta.days > threshold else " " + _s(delta.hours, "hour"))
    if delta.hours > 0:
        return _s(delta.hours, "hour") + ("" if short or delta.hours > threshold else " " + _s(delta.minutes, "minute"))
    if delta.minutes > 0:
        return _s(delta.minutes, "minute") + ("" if short or delta.minutes > threshold else " " + _s(delta.seconds, "second"))
    return _s(delta.seconds, "second")

def timedelta(starttime, endtime):
    return relativedelta.relativedelta(starttime, endtime)

def _absdelta(d):
    if d.seconds < 0 or d.minutes < 0 or d.hours < 0 or d.days < 0 or d.months < 0 or d.years < 0:
        return -d
    return d

# format a timedelta in human-readable format (e.g. "in 20 minutes" or "3 weeks ago")
@app.template_filter()
def humandelta(s, other = None):
    if other:
        # we got 2 datetimes
        return _delta(_absdelta(timedelta(other, s))).strip()


    if s.seconds < 0 or s.minutes < 0 or s.hours < 0 or s.days < 0 or s.months < 0 or s.years < 0:
        return "%s ago" % _delta(-s).strip()
    elif s.seconds > 0 or s.minutes > 0 or s.hours > 0 or s.days > 0 or s.months > 0 or s.years > 0:
        return "in %s" % _delta(s).strip()
    else:
        return s

@app.template_filter()
def humantime(s):
    diff = timedelta(s, datetime.utcnow())
    if diff.years < 1:
        return Markup('<span title="' + formattime(s) + '" class="time-title">' + humandelta(diff) + '</span>')
    else:
        return formattime(s)


@app.template_filter()
def epoch(s):
    # s = datetime.utcnow()
    return time.mktime(s.timetuple())

@app.template_filter()
def is_string(o):
    return type(o) == str

@app.template_filter()
def pathsplit(o):
    p = os.path.split(o)
    while len(p) > 0 and p[0] == "": p = p[1:]
    while len(p) > 0 and p[-1] == "": p = p[:-1]
    return p


@app.template_filter()
def gitToUser(gitUser):
    mail = Email.query.filter_by(address = gitUser.email).first()
    if mail:
        return mail.user
    return None

@app.template_filter()
def filetype(blob):
    if type(blob) == git.Tree:
        return "folder"

    if blob.size == 0:
        self._type = "empty"

    ext = extension(blob)
    mimetype = blob.mime_type

    IMAGE_TYPES = ("png", "jpg", "jpeg", "tga", "gif", "bmp")

    if ext in IMAGE_TYPES:
        return "image"

    if mimetype.split("/")[0] == "text":
        return "text"

    return "unknown"

@app.template_filter()
def extension(file):
    return splitext(file.name)[1][1:].lower()


@app.template_filter()
def diffLineType(line):
    if line[:3] == "---":
        return "from"
    elif line[:3] == "+++":
        return "to"
    elif line[:2] == "@@":
        return "section"
    elif line[:1] == "-":
        return "deletion"
    elif line[:1] == "+":
        return "insertion"
    return "context"

@app.template_filter()
def diffParseSection(line):
    m = re.search('^@@\s*-([0-9]+),[0-9]+\s+\+([0-9]+),[0-9]+\s*@@.*$', line)
    return (int(m.group(1)), int(m.group(2)))

