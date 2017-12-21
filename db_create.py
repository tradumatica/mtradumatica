#!venv/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db

import os.path

directory = os.path.dirname(SQLALCHEMY_DATABASE_URI[len("sqlite:///"):])

if not os.path.exists(directory):
    os.makedirs(directory)

db.create_all()
