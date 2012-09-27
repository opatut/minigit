from minigit import app
from flask import session, abort, request, flash

global current_user
current_user = None

def get_current_user():
    global current_user
    return current_user

class LoginRequired(Exception):
    def __init__(self, next = ""):
        self.message = "You need to be logged in to view this page."
        self.next = next

@app.before_request
def check_login():
    global current_user
    if "login_id" in session:
        from minigit.models import User
        current_user = User.query.filter_by(id = session["login_id"]).first()
        if not current_user:
            logout_now()
    else:
        current_user = None

    if not request.endpoint in ("index", "static", "login", "register"):
        require_login()

def login_as(user):
    session["login_id"] = user.id
    global current_user
    current_user = user

def logout_now():
    if "login_id" in session:
        session.pop("login_id")
    global current_user
    current_user = None

def require_login():
    if not current_user:
        raise LoginRequired(request.url)

def require_user(user):
    require_login()
    islist = isinstance(user, list)
    if (islist and not current_user in user) or (not islist and user != current_user):
        abort(403)

def require_admin():
    require_login()
    if not current_user.is_admin:
        abort(403)
