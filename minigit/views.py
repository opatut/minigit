import os
from datetime import datetime, timedelta

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort

from minigit import app, db
from minigit.models import *
from minigit.forms import *

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        login_as(user)
        flash("You successfully logged in.", category = "success")
        if form.next.data:
            return redirect(form.next.data)
        else:
            return redirect(url_for("index"))
    else:
        form.next.data = request.args.get("next", "")

    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    logout_now()
    flash("You were logged out.", category = "success")
    return redirect(url_for("login"))

@app.route("/list/")
def repositories():
    return render_template("repositories.html", list = Repository.query.all())

@app.route("/<slug>/")
def repository(slug):
    return redirect(url_for("browse", slug = slug, ref = "HEAD", path = ""))

@app.route("/not-implemented/")
def not_implemented():
    flash("This feature is not yet implemented.", category = "error")
    return redirect(url_for("index"))

@app.route("/<slug>/admin/permissions/")
def permissions(slug):
    repo = get_repo(slug)
    repo.requirePermission("admin")

    return render_template("repo/permissions.html", repo = repo)

@app.route("/<slug>/commits/")
@app.route("/<slug>/commits/<ref>/")
def commits(slug, ref = "HEAD"):
    repo = get_repo(slug)
    repo.requirePermission("read")

    return render_template("repo/commits.html", repo = repo, commits = repo.git.getCommits(ref))

@app.route("/<slug>/commit/<ref>/")
def commits_details(slug, ref):
    repo = get_repo(slug)
    repo.requirePermission("read")

    return render_template("repo/commit.html", repo = repo, commit = repo.git.getCommit(ref))

@app.route("/<slug>/browse/<ref>/")
@app.route("/<slug>/browse/<ref>/<path:path>")
def browse(slug, ref = "HEAD", path = ""):
    repo = get_repo(slug)
    repo.requirePermission("read")

    print "Showing %s" % path
    tree = repo.git.getTree(ref)
    node = tree.find(path)

    if not node:
        abort(404)

    if node.is_blob:
        return render_template("repo/file.html", repo = repo, ref = ref, path = path, file = node)
    elif node.is_tree:
        return render_template("repo/browse.html", repo = repo, ref = ref, path = path, tree = node)
    else:
        abort(404)

@app.route("/<slug>/raw/<ref>/<path:path>")
def file_content(slug, ref, path):
    repo = get_repo(slug)
    repo.requirePermission("read")

    tree = repo.git.getTree(ref)
    node = tree.find(path)

    if not node.is_blob:
        abort(404)

    response = app.make_response(node.content)
    response.mimetype = node.mimetype
    return response


# ERROR HANDLERS

@app.errorhandler(LoginRequired)
def login_required(exception):
    flash(exception.message, "error")
    return redirect(url_for('login', next = exception.next))

