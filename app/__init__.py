from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy

app    = Flask(__name__)
app.config.from_object('config')
babel  = Babel(app)
db     = SQLAlchemy(app)


import os.path

directory = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'][len("sqlite:///"):])

if not os.path.exists(directory):
    os.makedirs(directory)

if not os.path.exists(app.config['TMP_FOLDER']):
    os.makedirs(app.config['TMP_FOLDER'])

from app import views, models, tasks

db.create_all()
db.session.commit()


