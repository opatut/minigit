from minigit import app
import os

# format a timestamp in default format (0000-00-00 00:00:00)
@app.template_filter()
def formattime(s):
    return s.strftime("%Y-%m-%d %H:%M:%S")

@app.template_filter()
def is_string(o):
    return type(o) == str

@app.template_filter()
def pathsplit(o):
    p = os.path.split(o)
    while len(p) > 0 and p[0] == "": p = p[1:]
    while len(p) > 0 and p[-1] == "": p = p[:-1]
    return p

