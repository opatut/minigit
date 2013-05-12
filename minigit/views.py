import os
from datetime import datetime, timedelta

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort

from minigit import app, db
from minigit.models import *
from minigit.forms import *

@app.route("/")
def index():
    if get_current_user():
        return redirect(url_for("repositories"))
    else:
        return redirect(url_for("login"))

@app.route("/login", methods = ["POST", "GET"])
def login():
    if get_current_user():
        return redirect(url_for("index"))

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

    return render_template("login.html", form = form, registrations_enabled = app.config["REGISTRATION_ENABLED"])

@app.route("/logout")
def logout():
    logout_now()
    flash("You were logged out.", category = "success")
    return redirect(url_for("login"))

@app.route("/register", methods = ["POST", "GET"])
def register():
    current_user = get_current_user()

    if current_user and not current_user.is_admin:
        flash("You are already logged in.", category = "success")
        return redirect(url_for("index"))

    first_user = User.query.count() == 0
    form = RegistrationForm()

    if form.validate_on_submit():
        # Create the user
        user = User(form.username.data, form.password.data)
        user.is_admin = first_user
        db.session.add(user)
        db.session.commit()

        # Add email address
        user.addEmail(form.email.data, True, True)
        db.session.commit()

        # Goto login
        if current_user:
            flash("The user account has been created.", category = "success")
            return redirect(url_for("register"))
        else:
            flash("Your user account has been created. You can now log in.", category = "success")
            return redirect(url_for("login"))

    elif current_user and current_user.is_admin:
        flash("You can register new users because you are logged in as admin.", category = "info")

    return render_template("register.html", form = form, first_user = first_user)

@app.route("/create", methods = ["POST", "GET"])
def create_repository():
    require_login()

    form = CreateRepositoryForm()

    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = form.slug.data.strip()
        if not slug: slug = get_slug(title)
        clone_from = form.clone_from.data.strip()

        if get_repo(slug, False):
            flash("A repository with the slug <b>%s</b> does already exist." % slug, category = "error")
        else:
            repo = Repository(title, slug)
            db.session.add(repo)

            if clone_from:
                repo.cloneFrom(clone_from)
            else:
                repo.init()

            db.session.commit()

            repo.setUserPermission(get_current_user(), "admin")
            db.session.commit()
            return redirect(url_for("repository", slug = repo.slug))

    return render_template("repo/create.html", form = form)

@app.route("/list/repositories/")
def repositories():
    repos = Repository.query.order_by("LOWER(title)").all()
    from minigit.filters import gittime
    repos.sort(key = lambda repo: gittime(repo.git.heads[0].commit.authored_date) if repo.commits else repo.created, reverse = True)
    return render_template("repositories.html", list = repos)

@app.route("/list/users/")
def users():
    return render_template("users.html", list = User.query.all())

@app.route("/not-implemented/")
def not_implemented():
    flash("This feature is not yet implemented.", category = "error")
    return redirect(url_for("index"))

@app.route("/repo/<slug>/")
def repository(slug):
    return redirect(url_for("browse", slug = slug, rev = "master", path = ""))

@app.route("/repo/<slug>/admin/permissions/", methods = ["GET", "POST"])
def permissions(slug):
    repo = get_repo(slug)
    repo.requirePermission("admin")

    implicit_access = ImplicitAccessForm()
    add_user_permission = AddUserPermissionForm()

    if "implicit" in request.args and implicit_access.validate_on_submit():
        repo.implicit_access = implicit_access.level.data
        repo.implicit_guest_access = implicit_access.guest.data
        db.session.commit()
        flash("The implicit access setting has been saved.", category = "success")
    elif request.method == "GET":
        implicit_access.level.data = repo.implicit_access
        implicit_access.guest.data = repo.implicit_guest_access

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
@app.route("/repo/<slug>/commits/<rev>/")
def commits(slug, rev = "master"):
    repo = get_repo(slug)
    repo.requirePermission("read")
    commits = []
    for commit in repo.git.iter_commits(rev):
        commits.append(commit)

    return render_template("repo/commits.html", repo = repo, commits = commits)

@app.route("/repo/<slug>/commit/<rev>/")
def commits_details(slug, rev):
    repo = get_repo(slug)
    repo.requirePermission("read")

    commit = repo.getCommit(rev)
    if not commit: abort(404)

    return render_template("repo/commit.html", repo = repo, commit = commit)

@app.route("/repo/<slug>/browse/<rev>/")
@app.route("/repo/<slug>/browse/<rev>/<path:path>")
def browse(slug, rev = "master", path = ""):
    repo = get_repo(slug)
    repo.requirePermission("read")

    commit = repo.getCommit(rev)
    if not commit: abort(404)

    tree = commit.tree

    # TODO: parse path and apply to filter down to a tree
    target = tree
    if path:
        target = target / path.strip("/")

    if type(target) == git.Blob:
        return render_template("repo/file.html", repo = repo, rev = rev, path = path, file = target, commit = commit)
    elif type(target) == git.Tree:
        return render_template("repo/browse.html", repo = repo, rev = rev, path = path, tree = target, commit = commit)
    else:
        raise Exception("Why could we find something other than blob/tree by path filtering a commit object??? Weird!")

    #return render_template("repo/error.html", error = "empty", repo = repo)

@app.route("/repo/<slug>/raw/<rev>/<path:path>")
def file_content(slug, rev, path):
    repo = get_repo(slug)
    repo.requirePermission("read")

    commit = repo.getCommit(rev)
    if not commit: abort(404)

    blob = commit.tree / path
    response = app.make_response(blob.data_stream.read())
    response.mimetype = blob.mime_type
    return response

@app.route("/repo/<slug>/issues/")
def issues(slug):
    repo = get_repo(slug)
    repo.requirePermission("read")
    issues = repo.issues.all()
    issues.sort(key = lambda a: a.replies.first().created)
    return render_template("repo/issues.html", repo = repo, issues = issues)

@app.route("/repo/<slug>/issues/create/", methods = ["POST", "GET"])
def issue_create(slug):
    repo = get_repo(slug)
    repo.requirePermission("read")

    create_form = IssueCreateForm()

    if create_form.validate_on_submit():
        issue = Issue(repo, create_form.title.data)
        issue.reply(create_form.text.data)

        db.session.add(issue)
        db.session.commit()

        flash("The issue '%s' has been created successfully." % (issue), category = "success")
        return redirect(url_for("issue", slug = slug, number = issue.number))
    else:
        return render_template("repo/issue_create.html", repo = repo, create_form = create_form)

@app.route("/repo/<slug>/issues/<int:number>/", methods = ["POST", "GET"])
def issue(slug, number):
    repo = get_repo(slug)
    repo.requirePermission("read")
    issue = repo.issues.filter_by(number = number).first_or_404()

    reply_form = IssueReplyForm()
    toggle_open_form = IssueToggleOpenForm()
    tag_add_form = IssueTagAddForm()

    if reply_form.validate_on_submit():
        issue.reply(reply_form.text.data)
        if reply_form.submit_close.data:
            issue.close()
        db.session.commit()

    if toggle_open_form.validate_on_submit():
        if toggle_open_form.reopen.data:
            issue.reopen()
        elif toggle_open_form.close.data:
            issue.close()
        db.session.commit()

    if tag_add_form.validate_on_submit():
        t = tag_add_form.tag.data.strip()
        if t in repo.taglist:
            tag = repo.tags.filter_by(tag = t).first()
            tag.color = "#" + tag_add_form.color.data
        else:
            tag = IssueTag(t, "#" + tag_add_form.color.data, repo)
            db.session.add(tag)

        issue.tags.append(tag)
        db.session.commit()

    return render_template("repo/issue.html", repo = repo, issue = issue,
        reply_form = reply_form, toggle_open_form = toggle_open_form,
        tag_add_form = tag_add_form)

@app.route("/profile", methods = ["POST", "GET"])
@app.route("/profile/<username>")
def profile(username = ""):
    require_login()

    if not username:
        user = get_current_user()
    else:
        user = User.query.filter_by(username = username).first_or_404()

    pw_form = None
    user_form = None
    if user == get_current_user():
        pw_form = ChangePasswordForm()

        if pw_form.validate_on_submit():
            user.password = hash_password(pw_form.new.data)
            db.session.commit()
            flash("Your password has been saved.", category = "success")
            return redirect(user.url)

        user_form = ChangeUsernameForm()

        if user_form.validate_on_submit():
            user.username = user_form.username.data
            db.session.commit()
            flash("Your username has been changed.", category = "success")
            return redirect(user.url)

    return render_template("profile/view.html", user = user, pw_form = pw_form, user_form = user_form)


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

@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def error_page(error):
    return render_template("error.html", error = error)


