from flask import Flask
from datetime import *
# from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown

app = Flask(__name__)
# mail = Mail(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minigit.db'
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'CHANGE_ME'
app.config.from_pyfile('../minigit.cfg', silent=True)

db = SQLAlchemy(app)

Markdown(app, safe_mode="escape")

import minigit.views
import minigit.models
#import minigit.login

@app.context_processor
def inject():
    return dict(
        #current_user = minigit.login.get_current_user(),
        current_datetime = datetime.utcnow()
    )
