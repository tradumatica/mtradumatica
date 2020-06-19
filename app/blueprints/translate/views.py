from app import app, db
from app.utils import utils, user_utils
from app.models import TranslatorFromBitext, User, LanguageModel, TranslatorFromBitext
from app.utils import translate as mosestranslate
from app.utils import querymodels as qm
from app.utils import moses_service
from app.utils.dictionaries import search_dictionary

from flask import Blueprint, render_template, abort, request, jsonify, url_for, send_file
from flask_login import login_required, current_user
from flask_babel import _
from werkzeug import secure_filename
from sqlalchemy import not_

import json, os, tempfile

translate_blueprint = Blueprint('translate', __name__, template_folder='templates')

USER_LOGIN_ENABLED = user_utils.isUserLoginEnabled()

@translate_blueprint.route('/translate', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def text():
  data = [ t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).all() if t.mydatefinished != None]
  return render_template("translate.html", title = _("Translate"), data = data,
                         user = user_utils.get_user())

@translate_blueprint.route('/actions/translatechoose/<int:id>', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translatechoose(id):
  text = json.loads(request.data)['text'] #.encode("utf-8")
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    return jsonify(status = "Fail", message = "Translation engine not available")
  try:
    result = mosestranslate.translate(text, t.basename)
    return jsonify(status = "OK", text = result)
  except:
    pass

  return jsonify(status = "Fail", message = "Translation failed")

@translate_blueprint.route('/inspect')  
@utils.condec(login_required, USER_LOGIN_ENABLED)
def inspect():
  urlmoses = "http://"+("".join(url_for('index', _external=True).split(":")[0:2])).split("/")[2]+":"+str(app.config["MOSES_SERVICE_PORT"])+"/RPC2"
  moses_active = TranslatorFromBitext.query.filter(TranslatorFromBitext.moses_served == True).count() > 0
  all_users = {}
  for i in User.query.all():
    all_users[i.id] = i.email
  all_users[None]=""
  translators = [ t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).filter(not_(TranslatorFromBitext.basename.like("%;;;;%"))) if t.mydatefinished != None]
  all_real_translators = [t for t in TranslatorFromBitext.query.filter(not_(TranslatorFromBitext.basename.like("%;;;;%"))) if t.mydatefinished != None]
  language_m  = [ l for l in LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()).all() if l.mydatefinished != None]
  return render_template("inspect.html", title = _("Inspect"), trans = translators, lm = language_m, 
                         all_trans = all_real_translators,
                         user = user_utils.get_user(), urlmoses = urlmoses, moses_active = moses_active, all_users = all_users)

@translate_blueprint.route('/actions/query-lm', methods=["GET", "POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@translate_blueprint.route('/actions/query-tm', methods=["GET", "POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def query_tm():
  req_s = json.loads(request.data)
  tobj = TranslatorFromBitext.query.get(req_s['id'])
  file_tm = os.path.join(tobj.get_path()[0],"phrase-table.gz")

  if file_tm is not None:
    lines = qm.query_tm(req_s['text'], file_tm)
    outval = "".join(lines).strip()
    if outval == "":
      outval == "<Not found>"
  
    return jsonify(output=outval, status="OK")
  else:
    return jsonify(output="", status="Error")

@translate_blueprint.route('/actions/search-dictionary', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
  filename = t.basename + "/lex." + extension
  
  return jsonify(translations=search_dictionary(filename, word))

@translate_blueprint.route('/actions/translate-inspect', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translate_inspect():
  obj = request.json
  text = obj["text"]
  tid  = int(obj["tid"])
  t = TranslatorFromBitext.query.get(tid)
  return jsonify(mosestranslate.translate_trace(text, t.basename))

@translate_blueprint.route('/actions/moses-status')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@translate_blueprint.route('/actions/moses-activate/<int:engine_id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def moses_activate(engine_id):
  if not USER_LOGIN_ENABLED or (USER_LOGIN_ENABLED and current_user.admin):
    tfb = TranslatorFromBitext.query.get(engine_id)    
    moses_service.moses_start(tfb.basename)
    tfb.moses_served = True
    tfb.moses_served_port = app.config["MOSES_SERVICE_PORT"]
    db.session.commit()
    
  return jsonify(status="OK")

@translate_blueprint.route('/actions/moses-deactivate')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def moses_deactivate():
  if not USER_LOGIN_ENABLED or (USER_LOGIN_ENABLED and current_user.admin):
    moses_service.moses_stop()
    for tfb in TranslatorFromBitext.query.filter(TranslatorFromBitext.moses_served == True):
      tfb.moses_served = False
      tfb.moses_served_port = None
    db.session.commit()
  return jsonify(status="OK")


@app.route('/actions/translate-doc', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translate_doc():
  file        = request.files['file']
  filename    = file.filename
  doctype     = file.filename.split(".")[-1]
  id          = request.form['translatorsel2']
  tmx         = 'tmxDownload' in request.form
  mimetype    = file.content_type
  basename    = secure_filename(file.filename)
  
  srcfile = tempfile.NamedTemporaryFile(delete=False)
  srcfile.close()
  file.save(srcfile.name)

  translator  = TranslatorFromBitext.query.get(id)  
  
  bname = ".".join(basename.split(".")[:-1])
  if tmx:  
    fname = mosestranslate.translate_document_tmx(srcfile.name, translator.basename, doctype, bname, translator.lang1, translator.lang2)
    retval = send_file(fname, as_attachment=True, attachment_filename="{}-{}-{}.zip".format(bname , translator.lang1, translator.lang2))
      
    os.unlink(fname)
    os.unlink(srcfile.name)
    return retval    
  else:
    fname = mosestranslate.translate_document(srcfile.name, translator.basename, doctype)
    retval = send_file(fname, as_attachment=True, attachment_filename="{}-{}-{}.{}".format(bname, translator.lang1, translator.lang2, doctype))
  
    os.unlink(fname)
    os.unlink(srcfile.name)
    return retval

@app.route('/actions/translate-tmx', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translate_tmx():
  file        = request.files['file']
  filename    = file.filename
  doctype     = file.filename.split(".")[-1]
  id          = request.form['translatorsel3']
  mimetype    = file.content_type
  basename    = secure_filename(file.filename)
  
  srcfile = tempfile.NamedTemporaryFile(delete=False)
  srcfile.close()
  file.save(srcfile.name)

  translator  = TranslatorFromBitext.query.get(id)  
  
  bname = ".".join(basename.split(".")[:-1])
  
  fname = mosestranslate.translate_tmx(srcfile.name, translator.basename, translator.lang1, translator.lang2)
  retval = send_file(fname, as_attachment=True, attachment_filename="{}-{}-{}.tmx".format(bname , translator.lang1, translator.lang2))
  os.unlink(fname)
  os.unlink(srcfile.name)
  return retval    

@app.route('/actions/translate-text/<int:id>', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
                            user_id = user_utils.get_uid())
  db.session.add(translation)
  db.commit()
    
  return jsonify(task_id=task.id)

@app.route('/actions/status-translate/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def status_translate(id):
  #Get Translation from DB and task from celery
  trans = Translation.query.get(id)
  if trans is None:
    return jsonify(status = "not found")
  t = celerytasks.translate.AsyncResult(trans.task_id)
  if t.state in ['PENDING','PROGRESS']:
    return jsonify(status = "translating")
  else:
    return jsonify(status = "done")

  
@app.route('/actions/downloadresult/<string:filename>/<string:download_as>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def downloadresult(filename, download_as):
  fname = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
  retval = send_file(filename, as_attachment=True,attachment_filename=download_as)
  os.unlink(fname)
  return retval