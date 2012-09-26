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

@app.route("/list/repositories/")
def repositories():
    return render_template("repositories.html", list = Repository.query.all())

@app.route("/list/users/")
def users():
    return render_template("users.html", list = User.query.all())

@app.route("/not-implemented/")
def not_implemented():
    flash("This feature is not yet implemented.", category = "error")
    return redirect(url_for("index"))

@app.route("/repo/<slug>/")
def repository(slug):
    return redirect(url_for("browse", slug = slug, ref = "HEAD", path = ""))

@app.route("/repo/<slug>/admin/permissions/", methods = ["GET", "POST"])
def permissions(slug):
    repo = get_repo(slug)
    repo.requirePermission("admin")

    implicit_access = ImplicitAccessForm()
    add_user_permission = AddUserPermissionForm()

    if "implicit" in request.args and implicit_access.validate_on_submit():
        repo.implicit_access = implicit_access.level.data
        db.session.commit()
        flash("The implicit access setting has been saved.", category = "success")
    elif request.method == "GET":
        implicit_access.level.data = repo.implicit_access

    if "add" in request.args and add_user_permission.validate_on_submit():
        username = add_user_permission.username.data.strip()
        level = add_user_permission.level.data

        user = User.query.filter_by(username = username).first()

        if user == get_current_user():
            flash("You cannot edit your own permissions. Give another user admin rights and ask them to do it for you.", category = "error")
        else:
            repo.setUserPermission(user, level)
            db.session.commit()
            flash("The permission for <b>%s</b> has been set to <b>%s</b>." % (username, level), category = "success")

    return render_template("repo/permissions.html", repo = repo, implicit_access = implicit_access, add_user_permission = add_user_permission)

@app.route("/repo/<slug>/admin/permissions/<username>/<action>")
def permissions_action(slug, username, action):
    repo = get_repo(slug)
    repo.requirePermission("admin")

    user = User.query.filter_by(username = username).first_or_404()

    if user == get_current_user():
        flash("You cannot set your own permission down. Give another user admin rights and ask them to do it for you.", category = "error")
    else:
        if action == "remove":
            repo.clearUserPermission(user)
            db.session.commit()
            flash("The permission for <b>%s</b> has been reset to the implicit access level." % username, category = "success")
        elif action in ("none", "find", "read", "write", "admin"):
            repo.setUserPermission(user, action)
            db.session.commit()
            flash("The permission for <b>%s</b> has been set to <b>%s</b>." % (username, action), category = "success")
        else:
            abort(404)

    return redirect(url_for("permissions", slug = slug))


@app.route("/repo/<slug>/commits/")
@app.route("/repo/<slug>/commits/<ref>/")
def commits(slug, ref = "HEAD"):
    repo = get_repo(slug)
    repo.requirePermission("read")

    return render_template("repo/commits.html", repo = repo, commits = repo.git.getCommits(ref))

@app.route("/repo/<slug>/commit/<ref>/")
def commits_details(slug, ref):
    repo = get_repo(slug)
    repo.requirePermission("read")

    return render_template("repo/commit.html", repo = repo, commit = repo.git.getCommit(ref))

@app.route("/repo/<slug>/browse/<ref>/")
@app.route("/repo/<slug>/browse/<ref>/<path:path>")
def browse(slug, ref = "HEAD", path = ""):
    repo = get_repo(slug)
    repo.requirePermission("read")

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

@app.route("/repo/<slug>/raw/<ref>/<path:path>")
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

@app.route("/profile")
@app.route("/profile/<username>")
def profile(username = ""):
    require_login()

    if not username:
        user = get_current_user()
    else:
        user = User.query.filter_by(username = username).first_or_404()

    return render_template("profile/view.html", user = user)


@app.route("/profile/keys", methods = ["POST", "GET"])
def keys():
    require_login()
    form = AddPublicKeyForm()

    if form.validate_on_submit():
        get_current_user().addPublicKey(form.key.data, form.name.data)
        db.session.commit()
        generate_authorized_keys()
        flash("Your key <b>%s</b> has been added successfully." % form.name.data, category = "success")
        return redirect(url_for("keys"))

    return render_template("profile/keys.html", keys = PublicKey.query.filter_by(user_id = get_current_user().id).all(), form = form)

@app.route("/profile/keys/remove/<int:id>")
def keys_remove(id):
    key = PublicKey.query.filter_by(id = id).first_or_404()
    require_user(key.user)
    db.session.delete(key)
    db.session.commit()
    generate_authorized_keys()
    flash("Your key <b>%s</b> has been deleted." % key.name, category = "success")
    return redirect(url_for("keys"))


@app.route("/profile/emails", methods = ["POST", "GET"])
def emails():
    require_login()
    form = AddEmailForm()

    if form.validate_on_submit():
        get_current_user().addEmail(form.email.data, form.default.data, form.gravatar.data)
        db.session.commit()
        flash("Your email address <b>%s</b> has been added successfully." % form.email.data, category = "success")
        return redirect(url_for("emails"))

    return render_template("profile/emails.html", emails = Email.query.filter_by(user_id = get_current_user().id).all(), form = form)

@app.route("/profile/emails/<action>/<int:id>")
def emails_action(action, id):
    email = Email.query.filter_by(id = id).first_or_404()
    require_user(email.user)

    if action == "remove":
        if email.is_default or email.is_gravatar:
            flash("You cannot remove your default or gravatar email. Please make another email address the default / gravatar address.", category = "error")
        else:
            require_user(email.user)
            db.session.delete(email)
            db.session.commit()
            flash("Your email address <b>%s</b> has been deleted." % email.address, category = "success")
    elif action == "default":
        get_current_user().setDefaultEmail(email)
        db.session.commit()
        flash("The email address <b>%s</b> has been set as default." % email.address, category = "success")
    elif action == "gravatar":
        get_current_user().setGravatarEmail(email)
        db.session.commit()
        flash("The email address <b>%s</b> has been set for gravatar use." % email.address, category = "success")
    else:
        abort(404)

    return redirect(url_for("emails"))

# ERROR HANDLERS

@app.errorhandler(LoginRequired)
def login_required(exception):
    flash(exception.message, "error")
    return redirect(url_for('login', next = exception.next))

