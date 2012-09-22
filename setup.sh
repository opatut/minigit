#!/bin/bash
virtualenv -p python2 env
. env/bin/activate
pip install --upgrade flask flask-sqlalchemy flask-wtf flask-markdown iso8601 pytz pygments
# flask-mail flask-login python-dateutil requests
