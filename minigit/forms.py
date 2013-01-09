# -*- coding: utf-8 -*-

from flask.ext.wtf import Form, SubmitField, TextField, TextAreaField, PasswordField, SelectField, HiddenField, BooleanField, Required, Length, EqualTo, Optional, NumberRange, Email as EmailValidator, ValidationError, URL, Regexp
from flask.ext.wtf.html5 import EmailField

from minigit import app
from minigit import models
from minigit.util import *
from minigit.login import *

############## VALIDATORS ####################

class Not(object):
    def __init__(self, call, message = None):
        self.call = call
        self.message = message

    def __call__(self, form, field):
        errored = False
        try:
            self.call(form, field)
        except ValidationError:
            # there was an error, so don't do anything
            errored = True

        if not errored:
            raise ValidationError(self.call.message if self.message == None else self.message)

class UsernameExists(object):
    def __call__(self, form, field):
        u = models.User.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError("The username does not exist.")

class EmailExists(object):
    def __call__(self, form, field):
        u = models.Email.query.filter_by(address = field.data).first()
        if not u:
            raise ValidationError("The username does not exist.")

class PublicKeyExists(object):
    def __call__(self, form, field):
        u = models.PublicKey.query.filter_by(key = field.data.strip()).first()
        if not u:
            raise ValidationError("The public key does not exist.")

class LoginValidator(object):
    def __init__(self, pw_field, message_username = "The username or password is incorrect.", message_password = "The username or password is incorrect."):
        self.pw_field = pw_field
        self.message_username = message_username
        self.message_password = message_password

    def __call__(self, form, field):
        u = models.User.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError(self.message_username)
        elif u.password != hash_password(form[self.pw_field].data):
            raise ValidationError(self.message_password)

class PasswordValidator(object):
    def __init__(self, message = "Your password is incorrect."):
        self.message = message

    def __call__(self, form, field):
        u = get_current_user()
        if not u or u.password != hash_password(field.data):
            raise ValidationError(self.message)

class IsPublicKey(object):
    def __call__(self, form, field):
        if not verify_key(field.data.strip()):
            raise ValidationError("This is not a valid publickey.")

############## FORMS ####################

class LoginForm(Form):
    username = TextField("Username", validators=[LoginValidator("password")])
    password = PasswordField("Password")
    next = HiddenField("next")

class RegistrationForm(Form):
    username = TextField("Username", validators=[
        Required(),
        Regexp("[0-9a-zA-Z\-_]", message = "The username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Not(UsernameExists(), message = "That username already exists."),
        Length(min = 3, max = 32, message="You have to enter a username of 3 to 32 characters length.")])
    password = PasswordField("Password", validators=[Length(min = 6, message = "Please enter a password of at least 6 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])
    email = EmailField("Email Address", validators=[
        Required(),
        Not(EmailExists(), message = "That email address is already in use."),
        EmailValidator(message = "The email address you entered is invalid.")])

class AddUserPermissionForm(Form):
    username = TextField("Username", validators = [UsernameExists()])
    level = SelectField("Access Level", choices = [
        ("none", "None"),
        ("find", "Find"),
        ("read", "Read"),
        ("write", "Write"),
        ("admin", "Admin")])
    submit = SubmitField("Add")

class ImplicitAccessForm(Form):
    level = SelectField("Access Level", choices = [
        ("none", "None"),
        ("find", "Find"),
        ("read", "Read"),
        ("write", "Write"),
        ("admin", "Admin")])
    guest = BooleanField("Apply to unauthenticated users (guests) as well", default = False)
    submit = SubmitField("Save")

class AddPublicKeyForm(Form):
    key = TextAreaField("Public Key", validators = [
        Required(),
        IsPublicKey(),
        Not(PublicKeyExists(), message = "This public key is already in use by one of the users, possibly you!?")])
    name = TextField("Key Name", validators = [Required()])
    submit = SubmitField("Add")

class AddEmailForm(Form):
    email = EmailField("E-Mail Address", validators = [
        EmailValidator(message = "The email address you entered is invalid."),
        Not(EmailExists(), message = "This email address is already in use by one of the users, possibly you!?")])
    default = BooleanField("Set as default", default = False)
    gravatar = BooleanField("Use for gravatar", default = False)
    submit = SubmitField("Add")

class CreateRepositoryForm(Form):
    title = TextField("Title", validators = [Required()])
    slug = TextField("Slug", validators = [
        Optional(),
        Regexp("[0-9a-zA-Z\-_]", message = "The slug contains invalid characters. Only use alphanumeric characters, dashes and underscores.")])
    clone_from = TextField("Clone from URL", validators = [Optional()])

class ChangePasswordForm(Form):
    old = PasswordField("Current Password", validators = [PasswordValidator()])
    new = PasswordField("New Password", validators=[Length(min = 6, message = "Please enter a password of at least 6 characters.")])
    new2 = PasswordField("New Password, again", validators=[EqualTo("new", "Passwords do not match.")])


class ChangeUsernameForm(Form):
    username = TextField("New Username", validators=[
        Required(),
        Regexp("[0-9a-zA-Z\-_]", message = "The username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Not(UsernameExists(), message = "That username already exists."),
        Length(min = 3, max = 32, message="You have to enter a username of 3 to 32 characters length.")])
    password = PasswordField("Current Password", validators=[PasswordValidator()])
