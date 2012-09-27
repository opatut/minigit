#!/usr/bin/env python2

from minigit import db
from minigit.util import generate_authorized_keys

db.drop_all()
db.create_all()
db.session.commit()

generate_authorized_keys()
