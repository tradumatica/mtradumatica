from app import db
from app import app
from app.models import LanguageModel, MonolingualCorpus, Corpus, TranslatorFromBitext, Bitext, User
from app.utils import user_utils, utils, train, metrics
from app.utils import tasks as celerytasks
from app.utils import translate as mosestranslate

from flask import Blueprint, render_template, request, jsonify, abort, url_for, flash, redirect
from flask_login import login_required, current_user
from flask_babel import _
from datetime import datetime

import shutil
import tempfile
import os
import hashlib

USER_LOGIN_ENABLED = user_utils.isUserLoginEnabled()

train_blueprint = Blueprint('train', __name__, template_folder='templates')

@train_blueprint.route('/language_models', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def language_models():
  return render_template("language-models.html", title = _("Language models"),
                         user = user_utils.get_user())

@train_blueprint.route('/translators', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translators():

  data = Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).all()
  translators = [t for t in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).all() if t.mydatefinished != None]
  return render_template("translators.html", title = _("MT Engines"), data = data, translators = translators,
                         user = user_utils.get_user())

@train_blueprint.route('/actions/generate-share-link', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def generate_share_link():
  mt_id = request.form.get('id')
  mt = TranslatorFromBitext.query.filter_by(id=mt_id).first()

  if mt and mt.user_id == user_utils.get_uid():
    h = hashlib.blake2b()
    h.update("{}-{}-{}-{}".format(mt.user_id, mt.id, mt.basename, mt.name).encode('utf-8'))
    share_key = h.hexdigest()[:32]

    mt.share_key = share_key
    db.session.commit()

    return jsonify({ "result": 200, "share_url": url_for('train.grab_mt', _external=True, share_key=share_key) })
  else:
    return jsonify({ "result": -1 })

@train_blueprint.route('/translators/<string:share_key>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def grab_mt(share_key):
  mt = TranslatorFromBitext.query.filter_by(share_key=share_key).first()
  if mt and mt.user_id != user_utils.get_uid():
    new_mt_basename = mt.basename + "-" + share_key[:8]
    copy_mt_path = os.path.join(app.config['TRANSLATORS_FOLDER'], new_mt_basename)

    try:
      os.stat(copy_mt_path)
      flash(_('You have already imported this engine'), "danger")
    except:
      user = User.query.filter_by(id=mt.user_id).first()
      
      mt_copy = TranslatorFromBitext(name=mt.name, lang1=mt.lang1, lang2=mt.lang2, mydate=mt.mydate, mydatefinished=mt.mydatefinished, 
                  mydateopt=mt.mydateopt, mydateoptfinished=mt.mydateoptfinished, bitext_id=mt.bitext_id, 
                  languagemodel_id=mt.languagemodel_id, task_id=mt.task_id, task_opt_id=mt.task_opt_id, 
                  generated_id=mt.generated_id, basename=mt.basename, exitstatus=mt.exitstatus, moses_served=mt.moses_served, 
                  moses_served_port=mt.moses_served_port, size_mb=mt.size_mb, bleu=mt.bleu, chrf3=mt.chrf3, 
                  wer=mt.wer, ter=mt.ter, beer=mt.beer)

      mt_copy.user_id = user_utils.get_uid()
      mt_copy.name = mt.name + " [{}]".format(user.email if user else "")
      mt_copy.basename = new_mt_basename

      mt_path = os.path.join(app.config['TRANSLATORS_FOLDER'], mt.basename)
      
      os.mkdir(copy_mt_path)
      for file in os.listdir(mt_path):
        os.link(os.path.join(mt_path, file), os.path.join(copy_mt_path, file))

      db.session.add(mt_copy)
      db.session.commit()
  else:
    flash(_('The link you provided is invalid'), "danger")
  
  return redirect(url_for('train.translators'))

@train_blueprint.route('/actions/languagemodel-create/<string:parname>/<string:language1>/<string:monocorpusid>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def languagemodel_create(parname, language1, monocorpusid):
  #TODO: check existing monocorpus with the same name?

  #launch task, deal with filenames and so on
  monocorpus   = MonolingualCorpus.query.get(monocorpusid)
  t_id = train.lm_id_generator(language1)
  filename = train.build_lm_path(t_id,language1)

  lm = LanguageModel(name = parname, lang = language1, monocorpus_id = monocorpusid, 
                     path = filename, generated_id = t_id, user_id = user_utils.get_uid())
  db.session.add(lm)
  db.session.commit()

  task = celerytasks.train_lm.apply_async(args=[lm.id])

  lm.task_id = task.id
  lm.mydate = datetime.utcnow()
  db.session.add(lm)
  db.session.commit()

  return jsonify(status = "OK")

@train_blueprint.route('/actions/translator-create/<string:parname>/<string:language1>/<string:language2>/<string:bitextid>/<string:languagemodelid>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
                           user_id = user_utils.get_uid())
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@train_blueprint.route('/actions/translator-createfromfiles/<string:parname>/<int:file1id>/<int:file2id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translator_createfromfiles(parname, file1id, file2id):
  #TODO: check existing Translator with the same name?

  #launch task, deal with filenames and so on
  file1 = Corpus.query.get(file1id)
  file2 = Corpus.query.get(file2id)

  t_id = train.id_generator(file1.lang, file2.lang)
  filename = train.build_translator_basename(t_id, file1.lang, file2.lang)

  t = TranslatorFromBitext(name = parname, lang1 = file1.lang, lang2 = file2.lang, 
                           basename = filename, generated_id = t_id, user_id = user_utils.get_uid())
  db.session.add(t)
  db.session.commit()
  
  task = celerytasks.train_simple_smt.apply_async(args=[file1id, file2id, t.id])
  
  filename = train.build_translator_basename(t_id, file1.lang, file2.lang)

  t.mydate  = datetime.utcnow()
  t.task_id = task.id
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@train_blueprint.route('/actions/translator-createfromexisting/<string:parname>/<int:trans1id>/<int:trans2id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
                           generated_id = t_id_1, user_id = user_utils.get_uid())
  t.mydate = startdate
  t.mydatefinished = datetime.utcnow()
  t.exitstatus = 0
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@train_blueprint.route('/actions/languagemodel-plainlist')
@train_blueprint.route('/actions/languagemodel-plainlist/<string:language>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def languageModel_plain_list(language=None):
  files=[]
  if language != None:
    files= LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()).filter(LanguageModel.exitstatus == 0).filter(LanguageModel.lang == language)
  else:
    files= LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()).filter(LanguageModel.exitstatus == 0)
  return jsonify(data=[f.__json__() for f in files])

@train_blueprint.route('/actions/languagemodel-list', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    icons_running      = '<span id="running-{0}" class="glyphicon glyphicon-hourglass" aria-hidden="true"></span>'
    icons_finished      = '<span id="finished-{0}" class="glyphicon glyphicon-ok text-success" aria-hidden="true"></span>'
    icons_error      = '<span id="exiterror-{0}" class="glyphicon glyphicon-remove" aria-hidden="true"></span>'

    query = LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()) \
    .filter(LanguageModel.name.like(search_str)) \
    .order_by(utils.query_order(columns[order_col], order_dir))[start:start+length]

    data = []
    for c in query:
      data.append([
        checkbox.format(c.id), 
        c.name, 
        c.lang, 
        c.monocorpus.name if c.monocorpus != None else "", 
        c.mydate.strftime(date_fmt), 
        c.mydatefinished.strftime(date_fmt) if c.mydatefinished != None else "" ,
        icons_running.format(c.id) if celerytasks.train_lm.AsyncResult(c.task_id).state in ['PENDING', 'PROGRESS' ] else 
          (icons_finished.format(c.id) if str(c.exitstatus) == '0' else icons_error.format(c.id))
      ])

    return jsonify(draw = draw,
                   data = data,
                   recordsTotal = LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()).count(),
                   recordsFiltered = LanguageModel.query.filter(LanguageModel.user_id == user_utils.get_uid()).filter(LanguageModel.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@train_blueprint.route('/actions/change-lm', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def change_languagemodel():
  translator_id = request.form.get('translator_id')
  lm_id = request.form.get('lm_id')

  translator = TranslatorFromBitext.query.filter_by(id=translator_id).first()
  lm = LanguageModel.query.filter_by(id=lm_id).first()

  if translator and (lm or lm_id == "-1"):
    translator_path = os.path.join(app.config['TRANSLATORS_FOLDER'], translator.basename)
    current_lm_path = os.path.join(translator_path, 'LM.blm')
    original_lm_path = os.path.join(translator_path, 'LM.blm.original')
    new_lm_path = os.path.join(lm.path, 'LM.blm') if lm else original_lm_path

    try:
      os.stat(original_lm_path)
    except:
      os.link(current_lm_path, original_lm_path)
    
    os.remove(current_lm_path)
    os.link(new_lm_path, current_lm_path)

    translator.languagemodel_id = lm_id
    db.session.commit()

    return jsonify({ "result": 200 })
  else:
    return jsonify({ "result": -1 })

@train_blueprint.route('/actions/status-languagemodel/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def status_languagemodel(id):
  #Get LM from DB and task from celery
  lm = LanguageModel.query.get(id)
  if lm is None:
    return jsonify(status = "not found")
  t = celerytasks.train_lm.AsyncResult(lm.task_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = "training")
  else:
    return jsonify(status = "done")

@train_blueprint.route('/actions/status-translator/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def status_translator(id):
  #Get Translator from DB and task from celery
  t = TranslatorFromBitext.query.get(id)
  if t is None or t.task_id is None:
    return jsonify(status = "not found")
  t = celerytasks.train_smt.AsyncResult(t.task_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = "training")
  else:
    return jsonify(status = "done")

@train_blueprint.route('/actions/status-translator-optimization/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def status_translator_optimization(id):
  #Get Translator from DB and task from celery
  t = TranslatorFromBitext.query.get(id)
  if t is None:
    return jsonify(status = "not found")
  t = celerytasks.tune_smt.AsyncResult(t.task_opt_id)
  if t.state in ['PENDING','PROGRESS']:
    #date is currently ignored
    return jsonify(status = "training")
  else:
    return jsonify(status = "done")

@train_blueprint.route('/actions/translator-optimize/<int:translatorid>/<int:bitextid>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def translator_optimize(translatorid, bitextid):
  #In order to tune, create a TMP dir with a copy of the translator structure, run mert, and copy back the optimized moses.ini to
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

@train_blueprint.route('/actions/languagemodel-delete/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@train_blueprint.route('/actions/translator-delete/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@train_blueprint.route('/actions/optimization-kill/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
  
@train_blueprint.route('/actions/translator-list', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    data = [[checkbox.format(c.id),c.name + " <small><span class='text-muted'>[{}]</span></small>".format(c.basename), c.lang1+"-"+c.lang2, c.bitext.name if c.bitext != None else "", c.languagemodel.name if c.languagemodel != None else "" , c.mydate.strftime(date_fmt) if c.mydate != None else "", c.mydatefinished.strftime(date_fmt) if c.mydatefinished != None else "" , choose_optimization_cell(c) ,  evaluation_cell(c), choose_optimization_icons(c), 
            c.id, c.lang2  ]
            for c in TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).filter(TranslatorFromBitext.name.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).count(),
                   recordsFiltered = TranslatorFromBitext.query.filter(TranslatorFromBitext.user_id == user_utils.get_uid()).filter(TranslatorFromBitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

def choose_optimization_icons(trobj):
  icons_running  = '<span id="running-{0}" class="glyphicon glyphicon-hourglass" aria-hidden="true"></span>'
  icons_finished = '<span id="finished-{0}" class="glyphicon glyphicon-ok text-success" aria-hidden="true"></span>'
  icons_hidden   = ''

  if user_utils.get_user() != None and not current_user.admin:
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
  date_fmt   = '%Y-%m-%d %H:%M:%S'
  optimizeButtonDisabled= '<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm" disabled="disabled"> <span class="glyphicon glyphicon-wrench" aria-hidden="true"></span> '.format(trobj.id)+_('Optimize')+'</button>'
  optimizeButtonEnabled = '<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-wrench" aria-hidden="true"></span> '.format(trobj.id)+_('Optimize')+'</button>'
  optimizeButtonHidden  = ''
  if user_utils.get_user() != None and not current_user.admin:
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

def evaluation_cell(trobj):
  evaluateButtonDisabled = '<button type="button" id="button-evaluate-{}" class="btn btn-default btn-sm" disabled="disabled"><span class="glyphicon glyphicon-check" aria-hidden="true"></span> '.format(trobj.id)+_('Evaluate')+'</button>'
  evaluateButtonEnabled = '<button type="button" id="button-evaluate-{}" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-check" aria-hidden="true"></span> '.format(trobj.id)+_('Evaluate')+'</button>'
  evaluateButtonHidden  = ''
  
  return evaluateButtonEnabled + ("" if trobj.bleu == None else "<br/><small>BLEU: {:.2f}; chrF3: {:.2f};</small><br/> <small>TER: {:.2f}; WER: {:.2f};</small><br/><small>BEER: {:.2f}</small>".format(trobj.bleu,trobj.chrf3,trobj.ter,trobj.wer, trobj.beer))
  if user_utils.get_user() != None:
    return evaluateButtonHidden
  if trobj.task_id != None and celerytasks.train_smt.AsyncResult(trobj.task_id.state) in ['PENDING', 'PROGRESS']:
    return evaluateButtonDisabled
  else:
    return evaluateButtonEnabled + ("" if trobj.bleu == None else "<br/><small>BLEU: {:.2f}; chrF3: {:.2f};</small><br/> <small>TER: {:.2f}; WER: {:.2f};</small><br/><small>BEER: {:.2f}</small>".format(trobj.bleu,trobj.chrf3,trobj.ter,trobj.wer, trobj.beer))
    

@app.route('/actions/perform-evaluation-translator/<int:id>', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def perform_eval_translator(id):
    t = TranslatorFromBitext.query.get(id)
    
    reftemp = tempfile.NamedTemporaryFile(delete=False)
    reffile = request.files["htrans"]
    reforig = request.files["htrans"].filename
    refname = reftemp.name
    
    for i in reffile:
        reftemp.write(i)
    reftemp.close()

    text = request.files["src"].read()

    t = TranslatorFromBitext.query.get(id)
    if t is None:
      return jsonify(status = "Fail", message = "Engine not available")
    try:
      result = mosestranslate.translate(text.decode("utf-8"), t.basename)
    except Exception as e:
      print(e)
      result = ""
    
    
    mttemp = tempfile.NamedTemporaryFile(delete=False)
    mtname = mttemp.name
    mttemp.write(result.encode("utf-8"))
    mttemp.close()
    
    n1 = tempfile.NamedTemporaryFile(delete=False)
    n2 = tempfile.NamedTemporaryFile(delete=False)
    l1 = n1.name
    l2 = n2.name
    n1.close()
    n2.close()

    metrics.prepare_files(refname, mtname, l1, l2)        
    os.unlink(refname)
    os.unlink(mtname)
   
    t.bleu  = metrics.bleu(l1,l2)
    t.ter   = metrics.ter(l1,l2)
    t.wer   = metrics.wer(l1,l2)
    t.chrf3 = metrics.chrF3(l1,l2)
    t.beer  = metrics.beer(l1,l2)
    
    os.unlink(l1)
    os.unlink(l2)
    
    db.session.add(t)
    db.session.commit()
    
    return jsonify(status="OK")

