#!/bin/bash
virtualenv -p python2 env
. env/bin/activate
pip install --upgrade flask flask-sqlalchemy flask-wtf flask-markdown
# flask-mail flask-login python-dateutil requests
