from app import babel
from app import app
from app.models import Corpus
from app.utils import user_utils, languages

from flask_login import current_user
from flask import session, request

@babel.localeselector
def get_locale():
  if "LANGUAGES" not in app.config:
    return "en"
  if user_utils.isUserLoginEnabled() and current_user.is_authenticated and current_user.lang in list(app.config["LANGUAGES"].keys()):
    return current_user.lang  if current_user.lang != None else "en"
  elif 'lang' in session and session['lang'] in list(app.config["LANGUAGES"].keys()):
    return session['lang']
  else:
    result = request.accept_languages.best_match(list(app.config["LANGUAGES"].keys()))
  return result if result != None else "en"

def language_list():
  known_languages = set([c.lang for c in Corpus.query.filter(Corpus.user_id == user_utils.get_uid())])
  return [[i[0], i[1], False if i[0] not in known_languages else True] for i in languages.lang_select_list]
