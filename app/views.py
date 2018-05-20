import base64
import json
import languages
import os
import querymodels as qm
import magic
import moses_service
import regex
import shutil
import tasks as celerytasks
import tempfile
import tmxdigest
import train
import translate as mosestranslate
import utils

from app import app, db, login_manager, babel
from datetime import datetime
from dictionaries import search_dictionary
from flask import abort, flash, g, jsonify, redirect, render_template, request, Response, send_file, session, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized
from flask_login import login_user, logout_user, login_required, current_user
from flask.ext.babel import refresh, _
from random import randint
from sqlalchemy import asc, desc, not_
from sqlalchemy.orm.exc import NoResultFound
from werkzeug import secure_filename
from .models import Corpus, SMT, Translator, Bitext, AddCorpusBitext, MonolingualCorpus, AddCorpusMonoCorpus, LanguageModel, TranslatorFromBitext, Translation, User, OAuth

if app.config['OAUTHLIB_INSECURE_TRANSPORT']:
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

login_manager.login_view = 'google.login'
login_manager.login_message = ''

google_blueprint = make_google_blueprint(scope = ["profile", "email"])
if app.config["USER_LOGIN_ENABLED"]:
  app.register_blueprint(google_blueprint, url_prefix = '/google_login')
  google_blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user = current_user)

@babel.localeselector
def get_locale():
  if current_user.is_authenticated and current_user.lang in app.config["LANGUAGES"].keys():
    return current_user.lang  
  elif 'lang' in session and lang['session'] in app.config["LANGUAGES"].keys():
    return session['lang']
  else:
    result = request.accept_languages.best_match(app.config["LANGUAGES"].keys())
  return result

@app.route('/actions/switch-language/<string:langcode>')
def switch_language(langcode):
  if current_user.is_authenticated:
    current_user.lang = langcode
    db.session.commit()
  else:
    session['lang'] = langcode
    
  refresh();
  return redirect(request.referrer)


app.jinja_env.globals.update(get_locale = get_locale)
app.jinja_env.globals.update(LANGUAGES = app.config["LANGUAGES"])
app.jinja_env.globals.update(sorted = sorted)

def get_uid():
  if current_user.is_authenticated:
    return current_user.id
  return None

def get_user():
  if current_user.get_id() != None:
    return current_user
  else:
    return None

def query_order(column, type):
  if type == "asc":
    return asc(column)
  else:
    return desc(column)


def sort_language_pair(l1,l2):
  if l1 < l2:
    return l1,l2
  else:
    return l2,l1
    
def language_list():
  known_languages = set([c.lang for c in Corpus.query.filter(Corpus.user_id == get_uid())])
  return [[i[0], i[1], False if i[0] not in known_languages else True] for i in languages.lang_select_list]


@utils.condec(login_manager.user_loader, app.config['USER_LOGIN_ENABLED'])
def load_user(user_id):
  return User.query.get(int(user_id))

@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
  account_info = blueprint.session.get('/plus/v1/people/me')

  if account_info.ok:
    account_info_json = account_info.json()
    username  = account_info_json['displayName']
    social_id = account_info_json['id']
    email     = account_info_json['emails'][0]['value']
    lang      = get_locale()    
    query = User.query.filter_by(social_id=social_id, username = username, email = email, lang = lang)

    try:
      user = query.one()
    except NoResultFound:
      if not app.config["ENABLE_NEW_LOGINS"]:
        flash(_('New user logging is temporary disabled'), "warning")
        return False
      user = User(social_id = social_id, username = username, email = email)
      db.session.add(user)
      db.session.commit()

    # Update admins
    for i in app.config["ADMINS"]:
      try:
        adminuser = User.query.filter(User.email == i).one()
        adminuser.admin = True
      except NoResultFound:
        pass
        
    db.session.commit() 

    # Check bans
    if user.email in app.config["BANNED_USERS"]:
      flash(_('User temporary banned'), "danger")
      return False
      
    login_user(user)
    flash(_('You have been logged in successfully'), "success")
  
@app.route('/logout')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def logout():
    logout_user()
    flash(_('You logged out successfully'), 'success')
    return redirect(url_for('index'))
  

@app.route('/')
@app.route('/index')
#@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def index():
  
  return render_template("index.html", lsl = language_list(), title = _("Home"), 
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)


@app.route('/files', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def files():
  return render_template("files.html", lsl = language_list(), title = _("File manager"),
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)

@app.route('/bitexts', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitexts():
  data = Bitext.query.filter(Bitext.user_id == get_uid()).all()
  return render_template("bitexts.html", lsl = language_list(), title = _("Bitext manager"), data = data,
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)

@app.route('/monolingual_corpora', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingual_corpora():
  return render_template("monolingual-corpora.html", lsl = language_list(), title = _("Monolingual corpora"),
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)

@app.route('/language_models', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def language_models():
  return render_template("language-models.html", lsl = language_list(), title = _("Language models"),
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)

@app.route('/translators', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translators():

  data = Corpus.query.filter(Corpus.user_id == get_uid()).all()
  translators = [t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).all() if t.mydatefinished != None and t.exitstatus == 0]
  return render_template("translators.html", lsl = language_list(), title = _("Translators"), data = data, translators = translators,
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = get_user())

@app.route('/translate', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translate_page():
  data = [ t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).all() if t.mydatefinished != None and t.exitstatus == 0 ]
  return render_template("translate.html", lsl = language_list(), title = _("Translate"), data = data,
                         user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = current_user)

@app.route('/tasks', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def tasks():
  data = Corpus.query.filter(Corpus.user_id == get_uid()).all()
  return render_template("tasks.html", lsl = language_list(), title = _("Tasks"), data = data)

@app.route('/test', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def test():
  return render_template("test.html", lsl = language_list(), title = _("Test"))

@app.route('/dashboard', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def dashboard():
  return render_template("dashboard.html", lsl = language_list(), title = _("Dashboard"))

@app.route('/web_service', methods=["GET","POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def web_service():
  return render_template("web-service.html", lsl = language_list(), title = _("Web service"))


@app.route('/about', methods=["GET","POST"])
def about():
  return render_template("about.html", lsl = language_list(), title = _("About"))

@app.route('/contact', methods=["GET","POST"])
def contact():
  return render_template("contact.html", lsl = language_list(), title = _("Contact"))

@app.route('/inspect', methods=["GET"])  
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def inspect():
  urlmoses = "http://"+("".join(url_for('index', _external=True).split(":")[0:2])).split("/")[2]+":"+str(app.config["MOSES_SERVICE_PORT"])+"/RPC2"
  moses_active = TranslatorFromBitext.query.filter(TranslatorFromBitext.moses_served == True).count() > 0
  all_users = {}
  for i in User.query.all():
    all_users[i.id] = i.email
  all_users[None]=""
  translators = [ t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).filter(not_(TranslatorFromBitext.basename.like("%;;;;%"))) if t.mydatefinished != None and t.exitstatus == 0 ]
  all_real_translators = [t for t in TranslatorFromBitext.query.filter(not_(TranslatorFromBitext.basename.like("%;;;;%"))) if t.mydatefinished != None and t.exitstatus == 0 ]
  language_m  = [ l for l in LanguageModel.query.filter(LanguageModel.user_id == get_uid()).all() if l.mydatefinished != None and  l.exitstatus == 0]
  return render_template("inspect.html", lsl = language_list(), title = _("Inspect"), trans = translators, lm = language_m, 
                         all_trans = all_real_translators, user_login_enabled = app.config['USER_LOGIN_ENABLED'],
                         user = get_user(), urlmoses = urlmoses, moses_active = moses_active, all_users = all_users)

@app.route('/actions/query-lm', methods=["GET", "POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def query_lm():
  req_s = json.loads(request.data)
  file_lm = None
  if req_s['type'] == 'lm':
    lmobj = LanguageModel.query.get(req_s['id'])
    file_lm = lmobj.get_blm_path()
  elif req_s['type'] == 'translator':
    tobj = TranslatorFromBitext.query.get(req_s['id'])
    file_lm = os.path.join(tobj.get_path()[0],"LM.blm")
  
  if file_lm is not None:
    lines = qm.query_lm(req_s['text'], file_lm)
    return jsonify(output="".join(lines), status="OK")
  else:
    return jsonify(output="", status="Error")

@app.route('/actions/query-tm', methods=["GET", "POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def query_tm():
  req_s = json.loads(request.data)
  tobj = TranslatorFromBitext.query.get(req_s['id'])
  file_tm = os.path.join(tobj.get_path()[0],"phrase-table.minphr")

  if file_tm is not None:
    lines = qm.query_tm(req_s['text'], file_tm)
    outval = "".join(lines).strip()
    if outval == "":
      outval == "<Not found>"
  
    return jsonify(output=outval, status="OK")
  else:
    return jsonify(output="", status="Error")


@app.route('/actions/file-upload', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_upload():
  file     = request.files['file']
  basename = secure_filename(file.filename)

  try:
      os.stat(app.config['UPLOAD_FOLDER'])
  except:
      os.mkdir(app.config['UPLOAD_FOLDER'])       
  
  filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-{1}".format(randint(1,100000), basename))
  while os.path.exists(filename):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-{1}".format(randint(1,100000), basename))

  sz, nc, nw, nl, lang = utils.write_upload(file, filename)
  
  mime     = magic.Magic(mime=True)
  mimetype = mime.from_file(filename)
  
  if mimetype in ["application/xml", "text/xml"] and filename[-4:].lower() == ".tmx":
    for i in tmxdigest.tmx2txt_filelist(filename, filename):
      sz, nc, nw, nl, lang = utils.file_properties(i)
      mime     = magic.Magic(mime=True)
      mimetype = mime.from_file(i)
      basename = "-".join(secure_filename(os.path.basename(i)).split("-")[1:])
      c = Corpus(name = basename, mydate = datetime.utcnow(),
               lang = lang if mimetype[0:4] == u"text" else u'<binary>', nlines = nl, nwords = nw,
               nchars = nc, size = sz, path = i,
               type = mimetype, user_id = get_uid())

      db.session.add(c)
    db.session.commit()
    os.unlink(filename)
  else:
      
    c = Corpus(name = basename, mydate = datetime.utcnow(),
               lang = lang if mimetype[0:4] == u"text" else u'<binary>', nlines = nl, nwords = nw,
               nchars = nc, size = sz, path = filename,
               type = mimetype, user_id = get_uid())

    db.session.add(c)
    db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/bitext-create/<string:parname>/<string:language1>/<string:language2>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_create(parname,language1,language2):
  #TODO: check existing bitext with the same name?
  language1,language2=sort_language_pair(language1,language2)
  name=parname+"_"+language1+"_"+language2
  #create empty bitext
  basename = secure_filename(name)
  try:
      os.stat(app.config['UPLOAD_FOLDER'])
  except:
      os.mkdir(app.config['UPLOAD_FOLDER'])       

  
  dirname = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-bitext-{1}".format(randint(1,100000), basename))
  while os.path.exists(dirname):
    dirname = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-bitext-{1}".format(randint(1,100000), basename))
  os.mkdir(dirname)

  b = Bitext(name = parname , lang1 = language1, lang2 = language2, nlines = 0, 
             mydate  = datetime.utcnow(), path= dirname, user_id = get_uid())

  fd0=open(b.get_lang1_path(),'w')
  fd0.close()
  fd1=open(b.get_lang2_path(),'w')
  fd1.close()

  db.session.add(b)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/monolingualcorpus-create/<string:parname>/<string:language1>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualcorpus_create(parname,language1):
  #TODO: check existing monocorpus with the same name?

  name=parname+"_"+language1
  #create empty bitext
  basename = secure_filename(name)
  
  try:
      os.stat(app.config['UPLOAD_FOLDER'])
  except:
      os.mkdir(app.config['UPLOAD_FOLDER'])       

  filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-monolingualcorpus-{1}".format(randint(1,100000), basename))
  while os.path.exists(filename):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-monolingualcorpus-{1}".format(randint(1,100000), basename))
  fd0=open(filename,'w')
  fd0.close()

  m = MonolingualCorpus(name = parname, lang = language1, nlines=0, mydate = datetime.utcnow(), 
                        path = filename, user_id = get_uid())
  db.session.add(m)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/languagemodel-create/<string:parname>/<string:language1>/<string:monocorpusid>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def languagemodel_create(parname, language1, monocorpusid):
  #TODO: check existing monocorpus with the same name?

  #launch task, deal with filenames and so on
  monocorpus   = MonolingualCorpus.query.get(monocorpusid)
  t_id = train.lm_id_generator(language1)
  filename = train.build_lm_path(t_id,language1)

  lm = LanguageModel(name = parname, lang = language1, monocorpus_id = monocorpusid, 
                     path = filename, generated_id = t_id, user_id = get_uid())
  db.session.add(lm)
  db.session.commit()

  task = celerytasks.train_lm.apply_async(args=[lm.id])

  lm.task_id = task.id
  lm.mydate = datetime.utcnow()
  db.session.add(lm)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/translator-create/<string:parname>/<string:language1>/<string:language2>/<string:bitextid>/<string:languagemodelid>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_create(parname,language1, language2, bitextid, languagemodelid):
  #TODO: check existing Translator with the same name?
  #launch task, deal with filenames and so on
  bitext   = Bitext.query.get(bitextid)
  languagemodel = LanguageModel.query.get(languagemodelid)
  t_id = train.id_generator(language1,language2)
  task = celerytasks.train_smt.apply_async(args=[language1,language2, bitextid ,languagemodelid, t_id])
  filename = train.build_translator_basename(t_id,language1,language2)

  t = TranslatorFromBitext(name = parname, lang1 = language1, lang2 = language2, mydate = datetime.utcnow(), 
                           bitext_id = bitextid, languagemodel_id = languagemodelid , basename= filename, task_id = task.id,
                           user_id = get_uid())
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/translator-createfromfiles/<string:parname>/<int:file1id>/<int:file2id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_createfromfiles(parname, file1id, file2id):
  #TODO: check existing Translator with the same name?

  #launch task, deal with filenames and so on
  file1 = Corpus.query.get(file1id)
  file2 = Corpus.query.get(file2id)

  t_id = train.id_generator(file1.lang, file2.lang)
  filename = train.build_translator_basename(t_id, file1.lang, file2.lang)

  t = TranslatorFromBitext(name = parname, lang1 = file1.lang, lang2 = file2.lang, 
                           basename = filename, generated_id = t_id, user_id = get_uid())
  db.session.add(t)
  db.session.commit()
  
  task = celerytasks.train_simple_smt.apply_async(args=[file1id, file2id, t.id])
  
  filename = train.build_translator_basename(t_id, file1.lang, file2.lang)

  t.mydate  = datetime.utcnow()
  t.task_id = task.id
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/translator-createfromexisting/<string:parname>/<int:trans1id>/<int:trans2id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_createfromexisting(parname, trans1id, trans2id):
  tfb1 = TranslatorFromBitext.query.get(trans1id)
  tfb2 = TranslatorFromBitext.query.get(trans2id)

  t_id_1 = train.id_generator(tfb1.lang1, tfb1.lang2)
  f_id_1 = train.build_translator_basename(t_id_1, tfb1.lang1, tfb1.lang2)
  t_id_2 = train.id_generator(tfb2.lang1, tfb2.lang2)
  f_id_2 = train.build_translator_basename(t_id_2, tfb2.lang1, tfb2.lang2)

  startdate = datetime.utcnow()  

  utils.recursive_link(os.path.join(app.config["TRANSLATORS_FOLDER"], tfb1.basename), 
                       os.path.join(app.config["TRANSLATORS_FOLDER"], f_id_1))
  utils.recursive_link(os.path.join(app.config["TRANSLATORS_FOLDER"], tfb2.basename), 
                       os.path.join(app.config["TRANSLATORS_FOLDER"], f_id_2))
  
  t = TranslatorFromBitext(name=parname, lang1 = tfb1.lang1, lang2 = tfb2.lang2, 
                           basename="{};;;;{}".format(f_id_1, f_id_2),
                           generated_id = t_id_1, user_id = get_uid())
  t.mydate = startdate
  t.mydatefinished = datetime.utcnow()
  t.exitstatus = 0
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/bitext-add-files/<int:id>/<int:idfile1>/<int:idfile2>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_add_files(id,idfile1, idfile2):
  #DEBUG
  print "Appending files to bitext {0}: {1} and {2}".format(id,idfile1, idfile2)
  b = Bitext.query.get(id)
  c1 = Corpus.query.get(idfile1)
  c2 = Corpus.query.get(idfile2)

  #if both files contain a different number of lines, we truncate the longest one
  numNewLines=min(c1.nlines,c2.nlines)

  #append numNewLines to each file from the bitext
  fileToWrite=open(b.get_lang1_path(),"a")
  linesAppended=0
  for line in open(c1.path):
    fileToWrite.write(line)
    if linesAppended >= numNewLines:
      break
  fileToWrite.close()

  fileToWrite=open(b.get_lang2_path(),"a")
  for line in open(c2.path):
    fileToWrite.write(line)
    if linesAppended >= numNewLines:
      break
  fileToWrite.close()

  #add a new mapping between bitext and couple of files

  #get maximum position of elements appended to bitext
  prevPosition=0
  addActions = AddCorpusBitext.query.all()
  if len(addActions) > 0:
    prevPosition=max( addAction.position for addAction in addActions )
  newAddAction = AddCorpusBitext()
  newAddAction.position = prevPosition +1
  newAddAction.bitext = b.id
  newAddAction.corpus1 = c1.id
  newAddAction.corpus2 = c2.id
  db.session.add(newAddAction)

  #update number of lines of bitext in db
  b.nlines=b.nlines + numNewLines
  db.session.commit()

  return jsonify(status = "OK")


@app.route('/actions/monolingualcorpus-add-files/<int:id>/<int:idfile1>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualcorpus_add_files(id,idfile1):
  b = MonolingualCorpus.query.get(id)
  c1 = Corpus.query.get(idfile1)


  numNewLines=c1.nlines

  #append numNewLines to each file from the bitext
  fileToWrite=open(b.path,"a")
  linesAppended=0
  for line in open(c1.path):
    fileToWrite.write(line)
    if linesAppended >= numNewLines:
      break
  fileToWrite.close()

  #add a new mapping between monolingual corpus and file

  #get maximum position of elements appended to bitext
  prevPosition=0
  addActions = AddCorpusMonoCorpus.query.all()
  if len(addActions) > 0:
    prevPosition=max( addAction.position for addAction in addActions )
  newAddAction = AddCorpusMonoCorpus()
  newAddAction.position = prevPosition +1
  newAddAction.monocorpus = b.id
  newAddAction.corpus = c1.id
  db.session.add(newAddAction)

  #update number of lines of bitext in db
  b.nlines=b.nlines + numNewLines
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/file-plainlist')
@app.route('/actions/file-plainlist/<string:language>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_plain_list(language=None):
  files=[]
  if language != None:
    files = Corpus.query.filter(Corpus.user_id == get_uid()).filter(Corpus.lang == language)
  else:
    files = Corpus.query.filter(Corpus.user_id == get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])



@app.route('/actions/file-list', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_list():
  columns = [None, Corpus.name, Corpus.lang, Corpus.nlines, Corpus.nwords, Corpus.nchars, Corpus.mydate]
 # columns   = ['','name', 'lang', 'nlines', 'nwords', 'nchars', 'mydate']

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
#    order_str  = u'{0} {1}'.format(columns[order_col], order_dir)
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'

    icons      = u'<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="download-{0}" class="glyphicon glyphicon-download-alt" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang, c.nlines, c.nwords, c.nchars,
             c.mydate.strftime(date_fmt), icons.format(c.id)]
            for c in Corpus.query.filter(Corpus.user_id == get_uid()).filter(Corpus.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Corpus.query.filter(Corpus.user_id == get_uid()).count(),
                   recordsFiltered = Corpus.query.filter(Corpus.user_id == get_uid()).filter(Corpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/bitext-plainlist')
@app.route('/actions/bitext-plainlist/<string:language1>/<string:language2>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_plain_list(language1=None, language2=None):
  files=[]
  if language1 != None and language2 != None:
    #sort languages
    language1,language2=sort_language_pair(language1,language2)
    files= Bitext.query.filter(Bitext.user_id == get_uid()).filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  else:
    files= Bitext.query.filter(Bitext.user_id == get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])

@app.route('/actions/bitext-plainlist/<int:trid>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_plain_list_for_translator(trid):
  files=[]
  tr = TranslatorFromBitext.query.get(trid)
  if tr != None:
    #sort languages
    language1,language2=sort_language_pair(tr.lang1,tr.lang2)
    files= Bitext.query.filter(Bitext.user_id == get_uid()).filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  return jsonify(data=[f.__json__() for f in files])


@app.route('/actions/bitext-list', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_list():
  columns = [None, Bitext.name, Bitext.lang1 , Bitext.nlines, Bitext.mydate]
 # columns   = ['','name', 'lang', 'nlines', 'nwords', 'nchars', 'mydate']

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
#    order_str  = u'{0} {1}'.format(columns[order_col], order_dir)
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'

    icons      = u'<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="addtobitext-{0}-{1}-{2}" class="glyphicon glyphicon-plus-sign" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang1 +"-"+ c.lang2, c.nlines, c.mydate.strftime(date_fmt) ,  icons.format(c.id,c.lang1,c.lang2)]
            for c in Bitext.query.filter(Bitext.user_id == get_uid()).filter(Bitext.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Bitext.query.filter(Bitext.user_id == get_uid()).count(),
                   recordsFiltered = Bitext.query.filter(Bitext.user_id == get_uid()).filter(Bitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/monolingualcorpus-plainlist')
@app.route('/actions/monolingualcorpus-plainlist/<string:language>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualCorpus_plain_list(language=None):
  files=[]
  if language != None:
    files = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == get_uid()).filter(MonolingualCorpus.lang == language)
  else:
    files = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])


@app.route('/actions/monolingualcorpus-list', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualCorpus_list():
  columns = [None, MonolingualCorpus.name, MonolingualCorpus.lang , MonolingualCorpus.nlines, MonolingualCorpus.mydate]
 # columns   = ['','name', 'lang', 'nlines', 'nwords', 'nchars', 'mydate']

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
#    order_str  = u'{0} {1}'.format(columns[order_col], order_dir)
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'

    icons      = u'<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="addtomonocorpus-{0}-{1}" class="glyphicon glyphicon-plus-sign" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang, c.nlines, c.mydate.strftime(date_fmt) ,  icons.format(c.id,c.lang)]
            for c in MonolingualCorpus.query.filter(MonolingualCorpus.user_id == get_uid()).filter(MonolingualCorpus.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == get_uid()).count(),
                   recordsFiltered = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == get_uid()).filter(MonolingualCorpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/languagemodel-plainlist')
@app.route('/actions/languagemodel-plainlist/<string:language>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def languageModel_plain_list(language=None):
  files=[]
  if language != None:
    files= LanguageModel.query.filter(LanguageModel.user_id == get_uid()).filter(LanguageModel.exitstatus == 0).filter(LanguageModel.lang == language)
  else:
    files= LanguageModel.query.filter(LanguageModel.user_id == get_uid()).filter(LanguageModel.exitstatus == 0)
  return jsonify(data=[f.__json__() for f in files])

@app.route('/actions/languagemodel-list', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def languageModel_list():
  columns = [None, LanguageModel.name, LanguageModel.lang , None, LanguageModel.mydate, None]
 # columns   = ['','name', 'lang', 'nlines', 'nwords', 'nchars', 'mydate']

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
#    order_str  = u'{0} {1}'.format(columns[order_col], order_dir)
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'

    icons_running      = u'<span id="running-{0}" class="glyphicon glyphicon-hourglass" aria-hidden="true"></span>'
    icons_finished      = u'<span id="finished-{0}" class="glyphicon glyphicon-ok text-success" aria-hidden="true"></span>'
    icons_error      = u'<span id="exiterror-{0}" class="glyphicon glyphicon-remove" aria-hidden="true"></span>'


    data = [[checkbox.format(c.id), c.name, c.lang, c.monocorpus.name if c.monocorpus != None else "", c.mydate.strftime(date_fmt) , c.mydatefinished.strftime(date_fmt) if c.mydatefinished != None else "" , icons_running.format(c.id) if celerytasks.train_lm.AsyncResult(c.task_id).state in ['PENDING', 'PROGRESS' ] else (icons_finished.format(c.id) if c.exitstatus == 0 else icons_error.format(c.id) )] 
             for c in LanguageModel.query.filter(LanguageModel.user_id == get_uid()).filter(LanguageModel.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = LanguageModel.query.filter(LanguageModel.user_id == get_uid()).count(),
                   recordsFiltered = LanguageModel.query.filter(LanguageModel.user_id == get_uid()).filter(LanguageModel.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

def choose_optimization_icons(trobj):
  icons_running  = u'<span id="running-{0}" class="glyphicon glyphicon-hourglass" aria-hidden="true"></span>'
  icons_finished = u'<span id="finished-{0}" class="glyphicon glyphicon-ok text-success" aria-hidden="true"></span>'
  icons_hidden   = u''

  if get_user() != None and not current_user.admin:
    return icons_hidden
  if trobj.task_id != None and celerytasks.train_smt.AsyncResult(trobj.task_id).state in ['PENDING','PROGRESS']:
    #we do not print optimization icons if smt training is still running
    return icons_running.format(trobj.id)
  else:
    #training has finished, are we optimizing?
    if trobj.mydateopt == None:
      return icons_finished.format(trobj.id)
    else:
      if celerytasks.tune_smt.AsyncResult(trobj.task_opt_id).state in ['PENDING','PROGRESS']:
        return icons_running.format(trobj.id)
      else:
        return icons_finished.format(trobj.id)

def choose_optimization_cell(trobj):
  date_fmt   = u'%Y-%m-%d %H:%M:%S'
  optimizeButtonDisabled= u'<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm" disabled="disabled"> <span class="glyphicon glyphicon-wrench" aria-hidden="true"></span>'.format(trobj.id)+_('Optimize')+'</button>'
  optimizeButtonEnabled = u'<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-wrench" aria-hidden="true"></span>'.format(trobj.id)+_('Optimize')+'</button>'
  optimizeButtonHidden  = u''
  if get_user() != None and not current_user.admin:
    return optimizeButtonHidden
  if trobj.task_id != None and celerytasks.train_smt.AsyncResult(trobj.task_id).state in ['PENDING','PROGRESS']:
    #we do not print optimization icons if smt training is still running
    return optimizeButtonDisabled
  else:
    #training has finished, are we optimizing?
    if trobj.mydateopt == None:
      return optimizeButtonEnabled
    else:
      if celerytasks.tune_smt.AsyncResult(trobj.task_opt_id).state in ['PENDING','PROGRESS']:
        return trobj.mydateopt.strftime(date_fmt)+"#"
      else:
        return trobj.mydateopt.strftime(date_fmt)+"#"+trobj.mydateoptfinished.strftime(date_fmt)

@app.route('/actions/translator-list', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_list():
  #columns = [None, TranslatorFromBitext.name, TranslatorFromBitext.lang1 , Bitext.name , LanguageModel.name , TranslatorFromBitext.mydate]
  columns = [None, TranslatorFromBitext.name, TranslatorFromBitext.lang1 , None , None , TranslatorFromBitext.mydate, None, None ]

 # columns   = ['','name', 'lang', 'nlines', 'nwords', 'nchars', 'mydate']

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
#    order_str  = u'{0} {1}'.format(columns[order_col], order_dir)
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'

    data = [[checkbox.format(c.id),c.name, c.lang1+"-"+c.lang2, c.bitext.name if c.bitext != None else "", c.languagemodel.name if c.languagemodel != None else "" , c.mydate.strftime(date_fmt) , c.mydatefinished.strftime(date_fmt) if c.mydatefinished != None else "" , choose_optimization_cell(c) ,  choose_optimization_icons(c)  ]
            for c in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).filter(TranslatorFromBitext.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).count(),
                   recordsFiltered = TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == get_uid()).filter(TranslatorFromBitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/translator-optimize/<int:translatorid>/<int:bitextid>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_optimize(translatorid, bitextid):
  #In order to tune, create a TMP dir with a copy of the trasnlator structure, run mert, and copy back the optimized moses.ini to
  # the translator directory
  #we will need both SL and TL truecasing models

  #launch task, deal with filenames and so on
  tr = TranslatorFromBitext.query.get(translatorid)
  bitext = Bitext.query.get(bitextid)

  task = celerytasks.tune_smt.apply_async(args=[tr.lang1, tr.lang2, translatorid, bitext.id])

  tr.mydateopt = datetime.utcnow()
  tr.task_opt_id=task.id
  db.session.commit()

  return jsonify()

@app.route('/actions/file-delete/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_delete(id):
  corpus = Corpus.query.get(id)
  if corpus is None:
    abort(401)
    return
  try:
    os.unlink(corpus.path)
  except OSError:
    pass

  db.session.delete(corpus)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/bitext-delete/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_delete(id):
  bitext = Bitext.query.get(id)
  if bitext is None:
    abort(401)
    return
  try:
    shutil.rmtree(bitext.path)
  except OSError as e:
    print  e

  db.session.delete(bitext)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/monolingualcorpus-delete/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualcorpus_delete(id):
  monocorpus = MonolingualCorpus.query.get(id)
  if monocorpus is None:
    abort(401)
    return
  try:
    os.unlink(monocorpus.path)
  except OSError as e:
    print  e

  db.session.delete(monocorpus)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/languagemodel-delete/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def languagemodel_delete(id):
  lm = LanguageModel.query.get(id)
  if lm is None:
    abort(401)
    return

  #stop task
  task    = celerytasks.train_lm.AsyncResult(lm.task_id)
  if task.state == 'PROGRESS':
    pid     = task.info.get('proc_id', 0)
    tmpdir  = task.info.get('tmpdir', '')
    task.revoke(terminate=True)

    if train.is_proc_running(pid):
      train.kill_execution(pid, tmpdir)

  shutil.rmtree(lm.path, ignore_errors=True)

  db.session.delete(lm)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/translator-delete/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translator_delete(id):
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    abort(401)
    return

  #stop task
  if t.task_id != None:
    task  = celerytasks.train_smt.AsyncResult(t.task_id)
    if task.state == 'PROGRESS':
      pid     = task.info.get('proc_id', 0)
      tmpdir  = task.info.get('tmpdir', '')
      task.revoke(terminate=True)

      if train.is_proc_running(pid):
        train.kill_execution(pid, tmpdir)
  #optimization ongoing
  if t.task_opt_id != None:
    task  = celerytasks.train_smt.AsyncResult(t.task_opt_id)
    if task.state == 'PROGRESS':
      pid     = task.info.get('proc_id', 0)
      tmpdir  = task.info.get('tmpdir', '')
      task.revoke(terminate=True)

      if train.is_proc_running(pid):
        train.kill_execution(pid, tmpdir)

  for i in t.get_path():
    shutil.rmtree(i, ignore_errors=True)

  db.session.delete(t)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/optimization-kill/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def optimization_kill(id):
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    abort(401)
    return

  #stop task
  if t.task_opt_id != None:
    task  = celerytasks.train_smt.AsyncResult(t.task_opt_id)
    if task.state == 'PROGRESS':
      pid     = task.info.get('proc_id', 0)
      tmpdir  = task.info.get('tmpdir', '')
      task.revoke(terminate=True)

      if train.is_proc_running(pid):
        train.kill_execution(pid, tmpdir)
  
  t.mydateopt = None
  t.task_opt_id = None
  db.session.commit()
  return jsonify(status = "OK")
  

@app.route('/actions/file-download/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_download(id):

  def generate(c):
    f = open(c.path, "r")
    while True:
      data = f.read(1024)
      if not data:
        break
      yield data

    f.close()

  corpus = Corpus.query.get(id)
  return Response(generate(corpus), mimetype = corpus.type, headers = {"Content-Disposition":"attachment; filename={0}".format(corpus.name)})

@app.route('/actions/file-peek/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_peek(id):
  corpus = Corpus.query.get(id)

  f = open(corpus.path, "r")
  data = f.read(1024*20)
  f.close()

  result = []
  if data:
    result = data.split("\n")[0:20]

  return jsonify(lines = result, filename=corpus.name)

@app.route('/actions/monolingualcorpus-peek/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def monolingualcorpus_peek(id):
  corpus = MonolingualCorpus.query.get(id)

  f = open(corpus.path, "r")
  data = f.read(1024*20)
  f.close()

  result = []
  if data:
    result = data.split("\n")[0:20]

  return jsonify(lines = result, filename=corpus.name)

@app.route('/actions/bitext-peek/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def bitext_peek(id):
  corpus = Bitext.query.get(id)

  f1 = open(corpus.get_lang1_path(), "r")
  data1 = f1.read(1024*20)
  f1.close()

  f2 = open(corpus.get_lang2_path(), "r")
  data2 = f2.read(1024*20)
  f2.close()

  result1 = []
  result2 = []
  if data1 and data2:
    result1 = data1.split("\n")[0:20]
    result2 = data2.split("\n")[0:20]

  return jsonify(lines1 = result1, lines2=result2, filename=corpus.name)


@app.route('/actions/file-setlang/<int:id>/<string:code>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def file_setlang(id, code):
  corpus = Corpus.query.get(id)
  corpus.lang = code
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/status-simple')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def status_simple():
  if len(Translator.query.filter(Translator.user_id == get_uid()).all()) == 0:
    return jsonify(status = u"empty")

  t    = Translator.query.filter(Translator.user_id == get_uid()).one()
  task = celerytasks.train_simple_smt.AsyncResult(t.task_id)
  if task.state == 'PROGRESS':
    return jsonify(status = u"training", year = t.start.year, month = t.start.month, day = t.start.day,
                   hours = t.start.hour, minutes = t.start.minute, seconds = t.start.second)
  else:
    return jsonify(status = u"done")

@app.route('/actions/status-languagemodel/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def status_languagemodel(id):
  #Get LM from DB and task from celery
  lm = LanguageModel.query.get(id)
  if lm is None:
    return jsonify(status = u"not found")
  t = celerytasks.train_lm.AsyncResult(lm.task_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = u"training")
  else:
    return jsonify(status = u"done")

@app.route('/actions/status-translator/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def status_translator(id):
  #Get Translator from DB and task from celery
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    return jsonify(status = u"not found")
  t = celerytasks.train_smt.AsyncResult(t.task_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = u"training")
  else:
    return jsonify(status = u"done")

@app.route('/actions/status-translator-optimization/<int:id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def status_translator_optimization(id):
  #Get Translator from DB and task from celery
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    return jsonify(status = u"not found")
  t = celerytasks.tune_smt.AsyncResult(t.task_opt_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = u"training")
  else:
    return jsonify(status = u"done")


@app.route('/actions/cancel-simple')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def cancel_simple():
  t = Translator.query.one()
  task    = celerytasks.train_simple_smt.AsyncResult(t.task_id)
  pid     = task.info.get('proc_id', 0)
  tmpdir  = task.info.get('tmpdir', '')
  task.revoke(terminate=True)
  Translator.query.delete()
  db.session.commit()

  if train.is_proc_running(pid):
    train.kill_execution(pid, tmpdir)

  return jsonify(status = u"OK")

@app.route('/actions/remove-simple')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def remove_simple():
  t = Translator.query.one()
  shutil.rmtree(t.path, ignore_errors=True)
  Translator.query.delete()
  db.session.commit()
  # Directory cleanup
  return jsonify(status = u"OK")

@app.route('/actions/build-simple/<int:id1>/<int:id2>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def build_simple(id1, id2):
  c1   = Corpus.query.get(id1)
  c2   = Corpus.query.get(id2)
  t_id = train.id_generator(c1.lang,c2.lang)
  task = celerytasks.train_simple_smt.apply_async(args=[id1, id2, t_id])
  #TODO: use train.build_translator_path
  t_name    = "{0}-{1}-{2}".format(t_id, c1.lang, c2.lang)
  t_path    = os.path.join(app.config['TRANSLATORS_FOLDER'], t_name)

  t = Translator(name = t_name, task_id = task.id, path = t_path,sl = c1.lang, tl = c2.lang, 
                 start=datetime.utcnow(), user_id = get_uid())

  Translator.query.delete()
  db.session.add(t)
  db.session.commit()
  return jsonify(status = u"OK", task_id = task.id)

@app.route('/actions/translatechoose/<int:id>', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translatechoose(id):
  text = json.loads(request.data)['text'] #.encode("utf-8")
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    return jsonify(status = u"Fail", message = u"Translator not available")
  try:
    result = mosestranslate.translate(text, t.basename)
    return jsonify(status = u"OK", text = result)
  except:
    pass

  return jsonify(status = u"Fail", message = u"Translation failed")

@app.route('/actions/translate-doc/<int:id>', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translate_doc(id):
  file        = request.files['file']
  doctype     = request.form['doctype'] if 'doctype' != 'htm' else "html"
  mimetype    = file.content_type
  basename    = secure_filename(file.filename)
  translator  = TranslatorFromBitext.query.get(id)

  tmpdir      = translate.translate_dir_setup(file)
  task        = celerytasks.translate.apply_async(args=[tmpdir, translator.basename, doctype])
  
  translation = Translation(t_name   = translator.name, 
                            lang1    = translator.lang1, 
                            lang2    = translator.lang2,
                            f_name   = file.filename,
                            doctype  = mimetype, 
                            path     = tmpdir,
                            size     = os.path.getsize(os.path.join(tmpdir, "source")),
                            task_id  = task.id,
                            user_id  = get_uid())
  db.session.add(translation)
  db.commit()
    
  return jsonify(task_id=task.id)

@app.route('/actions/translate-text/<int:id>', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translate_text(id):
  file        = text = json.loads(request.data)['text']
  doctype     = "txt"
  mimetype    = "text/plain"
  basename    = secure_filename(file.filename)
  translator  = TranslatorFromBitext.query.get(id)

  tmpdir      = translate.translate_dir_setup(obj)
  task        = celerytasks.translate.apply_async(args=[tmpdir, translator.basename, doctype])
  
  translation = Translation(t_name  = translator.name, 
                            lang1   = translator.lang1, 
                            lang2   = translator.lang2, 
                            doctype = mimetype, 
                            path    = tmpdir,
                            size    = os.path.getsize(os.path.join(tmpdir, "source")),
                            task_id = task.id,
                            user_id = get_uid())
  db.session.add(translation)
  db.commit()
    
  return jsonify(task_id=task.id)
  
@app.route('/actions/downloadresult/<string:filename>/<string:download_as>', methods=["GET"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def downloadresult(filename, download_as):
  fname = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
  retval = send_file(filename, as_attachment=True,attachment_filename=download_as)
  os.unlink(fname)
  return retval
  
@app.route('/actions/testdownload')
def testdownload():
  return send_file("/etc/hosts", "text/plain", as_attachment=True)
  
@app.route('/actions/translate', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translate():
  text = json.loads(request.data)['text'].encode("utf-8")
  t = Translator.query.one()
  if t is None:
    return jsonify(status = u"Fail", message = u"Translator not available")
  try:
    result = mosestranslate.translate(text, t.name)
    return jsonify(status = u"OK", text = result)
  except:
    pass
  return jsonify(status = u"Fail", message = u"Translation failed")

@app.route('/actions/translate-inspect', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def translate_inspect():
  obj = request.json
  text = obj["text"]
  tid  = int(obj["tid"])
  t = TranslatorFromBitext.query.get(tid)
  return jsonify(mosestranslate.translate_trace(text, t.basename))

@app.route('/actions/search-dictionary', methods=["POST"])
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def search_dic():
  obj = request.json
  word = obj["word"]
  translator = int(obj["tid"])
  side = obj["side"]
  
  if side == "src":
    extension = "f2e"
  else:
    extension = "e2f"
  
  t = TranslatorFromBitext.query.get(translator)  
  filename = os.path.dirname(os.path.dirname(__file__)) + "/translators/" + t.basename + "/lex." + extension
  
  return jsonify(translations=search_dictionary(filename, word.encode("utf-8")))


@app.route('/ws/translate', methods=["POST"])
def ws_translate():
  obj  = request.json
  text = obj["text"]    if "text" in obj else ""
  type = obj["type"]    if "type" in obj else "txt"
  id   = int(obj["id"]) if "id"   in obj else -1
  name = obj["name"]    if "name" in obj else ""
  src  = obj["src"]     if "src"  in obj else ""
  trg  = obj["trg"]     if "trg"  in obj else ""
  
  if "type" in obj and obj["type"] not in mosestranslate.doctypes:
    return jsonify(message= "Document type '{0}' unsupported".format(obj["type"]), status = "FAIL")

  # Autodetect base64

  isBase64 = False
  if len(text) > 30:
    try:
      a = base64.decodestring(text)
      text = a
      isBase64 = True
    except binascii.Error:
      pass
  
  t = None
  if id != -1:
    t = TranslatorFromBitext.query.get(id)
  elif name != "":
    t = TranslatorFromBitext.query.filter(TranslatorFromBitext.name == name).first()
  elif src != "" and trg != "":
    t = TranslatorFromBitext.query.filter(TranslatorFromBitext.lang1 == src and TranslatorFromBitext.lang2 == trg).first()
  else:
    return jsonify(message = "Translator not available", status = "FAIL")
  
  if t == None:
    return jsonify(message = "Unknown error", status = "FAIL")
  else:
    result = mosestranslate.translate(text, t, type)
    if isBase64:
      result = base64.encodestring(result)    
    return jsonify(text = result, type = type, status = "OK")

  
@app.route('/ws/list')
def ws_list():
  tlist = []
  for t in TranslatorFromBitext.query.all():
    tlist.append({"id":t.id, "name":t.name, "src":t.lang1, "trg":t.lang2})
  return jsonify(list=tlist)

@app.route('/actions/moses-status')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def moses_alive():
  if not os.path.isfile(app.config["MOSES_SERVICE_PIDFILE"]):
    return jsonify(status="off", active=[])
  pid = -1
  with open(app.config["MOSES_SERVICE_PIDFILE"], "r") as pidf:
    pid = int(pidf.read())
  if pid == -1 or not utils.is_proc_alive(pid):
    return jsonify(status="off", active=[])
  if not utils.is_port_used(app.config["MOSES_SERVICE_PORT"]):
    return jsonify(status="off", active = [])

  active = []
  for tbf in TranslatorFromBitext.query.filter(TranslatorFromBitext.moses_served == True):
    active.append(tbf.id)
    
  if len(active) > 0:
    return jsonify(status="on", active = active)
        
  return jsonify(status="off", active = [])

@app.route('/actions/moses-activate/<int:engine_id>')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def moses_activate(engine_id):
  if not app.config["USER_LOGIN_ENABLED"] or (app.config["USER_LOGIN_ENABLED"] and current_user.admin):
    tfb = TranslatorFromBitext.query.get(engine_id)    
    moses_service.moses_start(tfb.basename)
    tfb.moses_served = True
    tfb.moses_served_port = app.config["MOSES_SERVICE_PORT"]
    db.session.commit()
    
  return jsonify(status="OK")

@app.route('/actions/moses-deactivate')
@utils.condec(login_required, app.config['USER_LOGIN_ENABLED'])
def moses_deactivate():
  if not app.config["USER_LOGIN_ENABLED"] or (app.config["USER_LOGIN_ENABLED"] and current_user.admin):
    moses_service.moses_stop()
    for tfb in TranslatorFromBitext.query.filter(TranslatorFromBitext.moses_served == True):
      tfb.moses_served = False
      tfb.moses_served_port = None
    db.session.commit()
  return jsonify(status="OK")
