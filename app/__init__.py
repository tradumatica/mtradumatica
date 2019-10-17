from flask import Flask
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app    = Flask(__name__, static_folder='static', static_url_path='', instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py', silent=True)

directory = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'][len("sqlite:///"):])

if not os.path.exists(directory):
    os.makedirs(directory)


app.secret_key = app.config['SECRET_KEY']
app.debug = app.config['DEBUG']

babel            = Babel(app)
db               = SQLAlchemy(app)
login_manager    = LoginManager(app)

if not os.path.exists(app.config['TMP_FOLDER']):
    os.makedirs(app.config['TMP_FOLDER'])

from app import views, models
from app.utils import tasks

db.create_all()
db.session.commit()


