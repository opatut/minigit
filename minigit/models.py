# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from hashlib import sha512, md5
from minigit import app, db
from flask import url_for, Markup

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    return s

def hash_password(s):
    return sha512((s + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(80), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    is_default = db.Column(db.Boolean)
    is_gravatar = db.Column(db.Boolean)

    def __init__(self, address, user):
        self.address = address
        self.user = user

class PublicKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(1024), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, key, user):
        self.key = key
        self.user = user

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))

    emails = db.relationship("Email", backref = "team", lazy = "dynamic")
    keys = db.relationship("PublicKey", backref = "user", lazy = "dynamic")

    is_admin = db.Column(db.Boolean, default=False)
    permissions = db.relationship("Permission", backref = "user", lazy = "dynamic")

    def __init__(self, username, password, is_admin = False):
        self.username = username
        self.password = hash_password(password)
        self.is_admin = is_admin

    def addEmail(self, email, default = False, gravatar = False):
        e = Email(email, self)
        db.session.add(e)
        self.emails.append(e)
        db.session.commit()

        if default: self.setDefaultEmail(e.id)
        if gravatar: self.setGravatarEmail(e.id)

    def addPublicKey(self, key):
        k = PublicKey(key, self)
        db.session.add(k)
        self.keys.append(k)

    def setDefaultEmail(self, id):
        if self.default_email:
            if self.default_email.id == id:
                return
            self.default_email.is_default = False
        Email.query.filter_by(id = id).first().is_default = True

    def setGravatarEmail(self, id):
        if self.gravatar_email:
            if self.gravatar_email.id == id:
                return
            self.gravatar_email.is_default = False
        Email.query.filter_by(id = id).first().is_gravatar = True

    @property
    def default_email(self):
        return Email.query.filter_by(user_id = self.id, is_default = True).first()

    @property
    def gravatar_email(self):
        return Email.query.filter_by(user_id = self.id, is_default = True).first()


    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def url(self, **values):
        return "#" # url_for('show_user', username = self.username, **values)

    @property
    def link(self):
        return Markup('<a href="{0}">{1}</a>'.format(self.url, self.username))

    def getAvatar(self, size = 32):
        # get gravatar email
        email = self.gravatar_email
        if not email: email = self.default_email

        return "http://www.gravatar.com/avatar/{0}?s={1}&d=identicon".format(md5(email.lower()).hexdigest(), size)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    repository = db.Column(db.Integer, db.ForeignKey("repository.id"))
    access = db.Column(db.Enum("none", "read", "write", "admin"), default = "none")

    def __init__(self, user, repository, access):
        self.user = user
        self.repository = repository
        self.access = access

class Repository(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    slug = db.Column(db.String(128))
    title = db.Column(db.String(128))

    def __init__(self, title, slug = ""):
        self.slug = get_slug(title) if not slug else slug
        self.title = title

    @property
    def path(self):
        return os.path.join(APP_CONFIG["home"], self.slug + ".git")

    def exists(self):
        return os.path.isdir(self.path)

    def create(self):
        pass
