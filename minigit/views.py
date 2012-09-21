from datetime import datetime, timedelta

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort

from minigit import app, db
from minigit.models import *

@app.route("/")
def index():
    return render_template("index.html")
