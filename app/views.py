import os
import psutil

from .utils import utils, user_utils, lang_utils

# Blueprints
from .blueprints.data.views import data_blueprint
from .blueprints.evaluation.views import evaluation_blueprint
from .blueprints.train.views import train_blueprint
from .blueprints.translate.views import translate_blueprint
from .blueprints.auth.views import auth_blueprint
from .blueprints.dashboard.views import dashboard_blueprint

from app import app, db, login_manager
from app.models import User
from flask import redirect, render_template, request, session, url_for
from flask_login import current_user
from flask_babel import _

blueprints = [auth_blueprint, data_blueprint,
              train_blueprint, translate_blueprint, 
              evaluation_blueprint, dashboard_blueprint]

for blueprint in blueprints:
  app.register_blueprint(blueprint)

app.jinja_env.globals.update(**{
  "get_locale": lang_utils.get_locale,
  "sorted": sorted,
  "len": len,
  "lsl": lang_utils.language_list,
  "user_login_enabled": user_utils.isUserLoginEnabled(),
  "cpu_count": psutil.cpu_count(),
  "cpu_percent": psutil.cpu_percent,
  "virtual_memory": psutil.virtual_memory,
  "disk_usage": psutil.disk_usage,
  "basedir": app.config['BASEDIR'],
  "tmp_folder": app.config['TMP_FOLDER'],
  "lms_folder": app.config['LMS_FOLDER'],
  "translators_folder": app.config['TRANSLATORS_FOLDER'],
  "upload_folder": app.config['UPLOAD_FOLDER'],
  "get_size": utils.get_size,
  "count_files": utils.count_files,
  "count_dirs": utils.count_dirs,
  "LANGUAGES": app.config["LANGUAGES"] if "LANGUAGES" in app.config else None
})

@app.route('/')
@app.route('/index')
def index():
  return render_template("index.html", title = _("Home"), 
                         user = user_utils.get_user())

@app.route('/actions/switch-language/<string:langcode>')
def switch_language(langcode):
  if "LANGUAGES" not in app.config or langcode not in app.config["LANGUAGES"]:
    return "en"
  if current_user.is_authenticated:
    current_user.lang = langcode
    db.session.commit()
  else:
    session['lang'] = langcode
    
  refresh()
  if request.referrer != None:
    return redirect(request.referrer)
  else:
    return redirect(url_for('index'))

@login_manager.user_loader
@utils.condec(login_manager.user_loader, user_utils.isUserLoginEnabled())
def load_user(user_id):
  return User.query.get(int(user_id))
