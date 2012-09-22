import os
from datetime import datetime, timedelta

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort

from minigit import app, db
from minigit.models import *

@app.route("/")
def index():
    return render_template("index.html")

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


@app.route("/<slug>/commits/")
@app.route("/<slug>/commits/<ref>/")
def commits(slug, ref = "HEAD"):
    repo = get_repo(slug)
    return render_template("repo/commits.html", repo = repo, commits = repo.git.getCommits(ref))

@app.route("/<slug>/commit/<ref>/")
def commits_details(slug, ref):
    repo = get_repo(slug)
    return render_template("repo/commit.html", repo = repo, commit = repo.git.getCommit(ref))

@app.route("/<slug>/browse/<ref>/")
@app.route("/<slug>/browse/<ref>/<path:path>")
def browse(slug, ref = "HEAD", path = ""):
    repo = get_repo(slug)
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
    tree = repo.git.getTree(ref)
    node = tree.find(path)

    if not node.is_blob:
        abort(404)

    response = app.make_response(node.content)
    response.mimetype = node.mimetype
    return response
