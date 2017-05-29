from app import app, db
from flask import request, render_template
from flask.ext.babel import gettext
from flask import jsonify
from flask import abort
from flask import Response
from flask import send_file
from werkzeug import secure_filename
import os
import langid
from datetime import datetime
import magic
from random import randint
from .models import Corpus, SMT, Translator, Bitext,AddCorpusBitext, MonolingualCorpus, AddCorpusMonoCorpus, LanguageModel,TranslatorFromBitext, Translation
import codecs
from sqlalchemy import asc, desc
import train
import tasks as celerytasks
import shutil
import regex
import translate as mosestranslate
import json, shutil
import languages
import tempfile
import querymodels as qm
import base64
from dictionaries import search_dictionary


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
  known_languages = set([c.lang for c in Corpus.query.all()])
  return [[i[0], i[1], False if i[0] not in known_languages else True] for i in languages.lang_select_list]

@app.route('/')
@app.route('/index')
def index():
  return render_template("index.html", lsl = language_list(), title = gettext("Home"))

@app.route('/files', methods=["GET","POST"])
def files():
  return render_template("files.html", lsl = language_list(), title = gettext("File manager"))

@app.route('/bitexts', methods=["GET","POST"])
def bitexts():
  data = Bitext.query.all()
  return render_template("bitexts.html", lsl = language_list(), title = gettext("Bitext manager"), data = data)

@app.route('/monolingual_corpora', methods=["GET","POST"])
def monolingual_corpora():
  return render_template("monolingual-corpora.html", lsl = language_list(), title = gettext("Monolingual corpora"))

@app.route('/language_models', methods=["GET","POST"])
def language_models():
  return render_template("language-models.html", lsl = language_list(), title = gettext("Language models"))

@app.route('/translators', methods=["GET","POST"])
def translators():
  data = Corpus.query.all()
  return render_template("translators.html", lsl = language_list(), title = gettext("Translators"), data = data)

@app.route('/translate', methods=["GET","POST"])
def translate_page():
  data = [ t for t in TranslatorFromBitext.query.all() if t.mydatefinished != None and t.exitstatus == 0 ]
  return render_template("translate.html", lsl = language_list(), title = gettext("Translate"), data = data)

@app.route('/tasks', methods=["GET","POST"])
def tasks():
  data = Corpus.query.all()
  return render_template("tasks.html", lsl = language_list(), title = gettext("Tasks"), data = data)

@app.route('/test', methods=["GET","POST"])
def test():
  return render_template("test.html", lsl = language_list(), title = gettext("Test"))

@app.route('/dashboard', methods=["GET","POST"])
def dashboard():
  return render_template("dashboard.html", lsl = language_list(), title = gettext("Dashboard"))

@app.route('/web_service', methods=["GET","POST"])
def web_service():
  return render_template("web-service.html", lsl = language_list(), title = gettext("Web service"))


@app.route('/about', methods=["GET","POST"])
def about():
  return render_template("about.html", lsl = language_list(), title = gettext("About"))

@app.route('/contact', methods=["GET","POST"])
def contact():
  return render_template("contact.html", lsl = language_list(), title = gettext("Contact"))

@app.route('/inspect', methods=["GET"])  
def inspect():
  translators = [ t for t in TranslatorFromBitext.query.all() if t.mydatefinished != None and t.exitstatus == 0 ]
  language_m  = [ l for l in LanguageModel.query.all() if l.mydatefinished != None and  l.exitstatus == 0]
  return render_template("inspect.html", lsl = language_list(), title = gettext("Inspect"), trans = translators, lm = language_m)

@app.route('/actions/query-lm', methods=["GET", "POST"])
def query_lm():
  req_s = json.loads(request.data)
  file_lm = None
  if req_s['type'] == 'lm':
    lmobj = LanguageModel.query.get(req_s['id'])
    file_lm = lmobj.get_blm_path()
  elif req_s['type'] == 'translator':
    tobj = TranslatorFromBitext.query.get(req_s['id'])
    file_lm = os.path.join(tobj.get_path(),"LM.blm")
  
  if file_lm is not None:
    lines = qm.query_lm(req_s['text'], file_lm)
    return jsonify(output="".join(lines), status="OK")
  else:
    return jsonify(output="", status="Error")

@app.route('/actions/query-tm', methods=["GET", "POST"])
def query_tm():
  req_s = json.loads(request.data)
  tobj = TranslatorFromBitext.query.get(req_s['id'])
  file_tm = os.path.join(tobj.get_path(),"phrase-table.minphr")

  if file_tm is not None:
    lines = qm.query_tm(req_s['text'], file_tm)
    outval = "".join(lines).strip()
    if outval == "":
      outval == "<Not found>"
  
    return jsonify(output=outval, status="OK")
  else:
    return jsonify(output="", status="Error")


@app.route('/actions/file-upload', methods=["POST"])
def file_upload():
  file     = request.files['file']
  basename = secure_filename(file.filename)

  filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-{1}".format(randint(1,100000), basename))
  while os.path.exists(filename):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-{1}".format(randint(1,100000), basename))

  output   = open(filename, 'w')

  sz = 0
  nc = 0
  nw = 0
  nl = 0
  excerpt = []
  lang = u""
  for i in file:
    output.write(i)
    sz += len(i)

    s = unicode(i, errors='ignore')
    nl += 1
    nw += len(s.split())
    nc += len(s)

    if nl < 1000:
      excerpt.append(s)
    elif nl == 1000:
      lang = langid.classify(u"".join(excerpt))[0]

  output.close()

  if nl < 1000:
    lang = langid.classify(u"".join(excerpt))[0]

  mime     = magic.Magic(mime=True)
  mimetype = mime.from_file(filename)


  c = Corpus(name = basename, mydate = datetime.utcnow(),
             lang = lang if mimetype[0:4] == u"text" else u'<binary>', nlines = nl, nwords = nw,
             nchars = nc, size = sz, path = filename,
             type = mimetype)

  db.session.add(c)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/bitext-create/<string:parname>/<string:language1>/<string:language2>')
def bitext_create(parname,language1,language2):
  #TODO: check existing bitext with the same name?
  language1,language2=sort_language_pair(language1,language2)
  name=parname+"_"+language1+"_"+language2
  #create empty bitext
  basename = secure_filename(name)
  dirname = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-bitext-{1}".format(randint(1,100000), basename))
  while os.path.exists(dirname):
    dirname = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-bitext-{1}".format(randint(1,100000), basename))
  os.mkdir(dirname)

  b = Bitext(name=parname , lang1 = language1, lang2 = language2, nlines=0, mydate  = datetime.utcnow(), path= dirname)

  fd0=open(b.get_lang1_path(),'w')
  fd0.close()
  fd1=open(b.get_lang2_path(),'w')
  fd1.close()

  db.session.add(b)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/monolingualcorpus-create/<string:parname>/<string:language1>')
def monolingualcorpus_create(parname,language1):
  #TODO: check existing monocorpus with the same name?

  name=parname+"_"+language1
  #create empty bitext
  basename = secure_filename(name)
  filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-monolingualcorpus-{1}".format(randint(1,100000), basename))
  while os.path.exists(filename):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], "{0:05d}-monolingualcorpus-{1}".format(randint(1,100000), basename))
  fd0=open(filename,'w')
  fd0.close()

  m = MonolingualCorpus(name=parname , lang = language1, nlines=0, mydate  = datetime.utcnow(), path= filename)
  db.session.add(m)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/languagemodel-create/<string:parname>/<string:language1>/<string:monocorpusid>')
def languagemodel_create(parname,language1, monocorpusid):
  #TODO: check existing monocorpus with the same name?

  #launch task, deal with filenames and so on
  monocorpus   = MonolingualCorpus.query.get(monocorpusid)
  t_id = train.lm_id_generator(language1)
  task = celerytasks.train_lm.apply_async(args=[monocorpus, t_id])
  filename = train.build_lm_path(t_id,language1)

  m = LanguageModel(name=parname , lang = language1,  mydate  = datetime.utcnow(), monocorpus_id = monocorpusid, path= filename, task_id = task.id)
  db.session.add(m)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/translator-create/<string:parname>/<string:language1>/<string:language2>/<string:bitextid>/<string:languagemodelid>')
def translator_create(parname,language1, language2, bitextid, languagemodelid):
  #TODO: check existing Translator with the same name?
  #launch task, deal with filenames and so on
  bitext   = Bitext.query.get(bitextid)
  languagemodel = LanguageModel.query.get(languagemodelid)
  t_id = train.id_generator(language1,language2)
  task = celerytasks.train_smt.apply_async(args=[language1,language2,bitext,languagemodel, t_id])
  filename = train.build_translator_basename(t_id,language1,language2)

  t = TranslatorFromBitext(name=parname , lang1 = language1, lang2 = language2, mydate  = datetime.utcnow(), bitext_id = bitextid, languagemodel_id = languagemodelid , basename= filename, task_id = task.id)
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/translator-createfromfiles/<string:parname>/<int:file1id>/<int:file2id>')
def translator_createfromfiles(parname,file1id, file2id):
  #TODO: check existing Translator with the same name?

  #launch task, deal with filenames and so on
  file1= Corpus.query.get(file1id)
  file2 = Corpus.query.get(file2id)

  t_id = train.id_generator(file1.lang,file2.lang)
  task = celerytasks.train_simple_smt.apply_async(args=[file1,file2, t_id])
  filename = train.build_translator_basename(t_id,file1.lang,file2.lang)

  t = TranslatorFromBitext(name=parname, lang1 = file1.lang, lang2 = file2.lang, mydate  = datetime.utcnow() , basename= filename, task_id = task.id)
  db.session.add(t)
  db.session.commit()

  return jsonify(status = "OK")


@app.route('/actions/bitext-add-files/<int:id>/<int:idfile1>/<int:idfile2>')
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
def file_plain_list(language=None):
  files=[]
  if language != None:
    files= Corpus.query.filter(Corpus.lang == language)
  else:
    files= Corpus.query.all()
  return jsonify(data=[f.serialize() for f in files])



@app.route('/actions/file-list', methods=["POST"])
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
            for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Corpus.query.count(),
                   recordsFiltered = Corpus.query.filter(Corpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/bitext-plainlist')
@app.route('/actions/bitext-plainlist/<string:language1>/<string:language2>')
def bitext_plain_list(language1=None, language2=None):
  files=[]
  if language1 != None and language2 != None:
    #sort languages
    language1,language2=sort_language_pair(language1,language2)
    files= Bitext.query.filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  else:
    files= Bitext.query.all()
  return jsonify(data=[f.serialize() for f in files])

@app.route('/actions/bitext-plainlist/<int:trid>')
def bitext_plain_list_for_translator(trid):
  files=[]
  tr = TranslatorFromBitext.query.get(trid)
  if tr != None:
    #sort languages
    language1,language2=sort_language_pair(tr.lang1,tr.lang2)
    files= Bitext.query.filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  return jsonify(data=[f.serialize() for f in files])


@app.route('/actions/bitext-list', methods=["POST"])
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
            for c in Bitext.query.filter(Bitext.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Bitext.query.count(),
                   recordsFiltered = Bitext.query.filter(Bitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/monolingualcorpus-plainlist')
@app.route('/actions/monolingualcorpus-plainlist/<string:language>')
def monolingualCorpus_plain_list(language=None):
  files=[]
  if language != None:
    files= MonolingualCorpus.query.filter(MonolingualCorpus.lang == language)
  else:
    files= MonolingualCorpus.query.all()
  return jsonify(data=[f.serialize() for f in files])


@app.route('/actions/monolingualcorpus-list', methods=["POST"])
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
            for c in MonolingualCorpus.query.filter(MonolingualCorpus.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = MonolingualCorpus.query.count(),
                   recordsFiltered = MonolingualCorpus.query.filter(MonolingualCorpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/languagemodel-plainlist')
@app.route('/actions/languagemodel-plainlist/<string:language>')
def languageModel_plain_list(language=None):
  files=[]
  if language != None:
    files= LanguageModel.query.filter(LanguageModel.exitstatus == 0).filter(LanguageModel.lang == language)
  else:
    files= LanguageModel.query.filter(LanguageModel.exitstatus == 0)
  return jsonify(data=[f.serialize() for f in files])

@app.route('/actions/languagemodel-list', methods=["POST"])
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


    data = [[checkbox.format(c.id), c.name, c.lang, c.monocorpus.name if c.monocorpus != None else "", c.mydate.strftime(date_fmt) , c.mydatefinished.strftime(date_fmt) if c.mydatefinished != None else "" , icons_running.format(c.id) if celerytasks.train_lm.AsyncResult(c.task_id).state in ['PENDING', 'PROGRESS' ] else (icons_finished.format(c.id) if c.exitstatus == 0 else icons_error.format(c.id) )] for c in LanguageModel.query.filter(LanguageModel.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = LanguageModel.query.count(),
                   recordsFiltered = LanguageModel.query.filter(LanguageModel.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

def choose_optimization_icons(trobj):
  icons_running      = u'<span id="running-{0}" class="glyphicon glyphicon-hourglass" aria-hidden="true"></span>'
  icons_finished      = u'<span id="finished-{0}" class="glyphicon glyphicon-ok text-success" aria-hidden="true"></span>'

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
  optimizeButtonDisabled=u'<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm" disabled="disabled"> <span class="glyphicon glyphicon-wrench" aria-hidden="true"></span> Optimize</button>'.format(trobj.id)
  optimizeButtonEnabled=u'<button type="button" id="button-optimize-{0}" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-wrench" aria-hidden="true"></span> Optimize</button>'.format(trobj.id)
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
            for c in TranslatorFromBitext.query.filter(TranslatorFromBitext.name.like(search_str)).order_by(query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = TranslatorFromBitext.query.count(),
                   recordsFiltered = TranslatorFromBitext.query.filter(TranslatorFromBitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@app.route('/actions/translator-optimize/<int:translatorid>/<int:bitextid>')
def translator_optimize(translatorid,bitextid):
  #In order to tune, create a TMP dir with a copy of the trasnlator structure, run mert, and copy back the optimized moses.ini to
  # the translator directory
  #we will need both SL and TL truecasing models

  #launch task, deal with filenames and so on
  tr= TranslatorFromBitext.query.get(translatorid)
  bitext = Bitext.query.get(bitextid)

  task = celerytasks.tune_smt.apply_async(args=[tr.lang1, tr.lang2,tr,bitext])

  tr.mydateopt = datetime.utcnow()
  tr.task_opt_id=task.id
  db.session.commit()





  return jsonify()

@app.route('/actions/file-delete/<int:id>')
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
def translator_delete(id):
  t =  TranslatorFromBitext.query.get(id)
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

  shutil.rmtree(t.get_path(), ignore_errors=True)

  db.session.delete(t)
  db.session.commit()
  return jsonify(status = "OK")

@app.route('/actions/file-download/<int:id>')
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
def file_setlang(id, code):
  corpus = Corpus.query.get(id)
  corpus.lang = code
  db.session.commit()

  return jsonify(status = "OK")

@app.route('/actions/status-simple')
def status_simple():
  if len(Translator.query.all()) == 0:
    return jsonify(status = u"empty")

  t    = Translator.query.one()
  task = celerytasks.train_simple_smt.AsyncResult(t.task_id)
  if task.state == 'PROGRESS':
    return jsonify(status = u"training", year = t.start.year, month = t.start.month, day = t.start.day,
                   hours = t.start.hour, minutes = t.start.minute, seconds = t.start.second)
  else:
    return jsonify(status = u"done")

@app.route('/actions/status-languagemodel/<int:id>')
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
def remove_simple():
  t = Translator.query.one()
  shutil.rmtree(t.path, ignore_errors=True)
  Translator.query.delete()
  db.session.commit()
  # Directory cleanup
  return jsonify(status = u"OK")

@app.route('/actions/build-simple/<int:id1>/<int:id2>')
def build_simple(id1, id2):
  c1   = Corpus.query.get(id1)
  c2   = Corpus.query.get(id2)
  t_id = train.id_generator(c1.lang,c2.lang)
  task = celerytasks.train_simple_smt.apply_async(args=[c1, c2, t_id])
  #TODO: use train.build_translator_path
  t_name    = "{0}-{1}-{2}".format(t_id, c1.lang, c2.lang)
  t_path    = os.path.join(app.config['TRANSLATORS_FOLDER'], t_name)

  t = Translator(name = t_name, task_id = task.id, path = t_path,sl = c1.lang, tl = c2.lang, start=datetime.utcnow())

  Translator.query.delete()
  db.session.add(t)
  db.session.commit()
  return jsonify(status = u"OK", task_id = task.id)


@app.route('/actions/translatechoose/<int:id>', methods=["POST"])
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
                            task_id  = task.id)
  db.session.add(translation)
  db.commit()
    
  return jsonify(task_id=task.id)

@app.route('/actions/translate-text/<int:id>', methods=["POST"])
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
                            task_id = task.id)
  db.session.add(translation)
  db.commit()
    
  return jsonify(task_id=task.id)



  
@app.route('/actions/downloadresult/<string:filename>/<string:download_as>', methods=["GET"])
def downloadresult(filename, download_as):
  fname = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
  retval = send_file(filename, as_attachment=True,attachment_filename=download_as)
  os.unlink(fname)
  return retval
  
@app.route('/actions/testdownload')
def testdownload():
  return send_file("/etc/hosts", "text/plain", as_attachment=True)
  
@app.route('/actions/translate', methods=["POST"])
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
def translate_inspect():
  obj = request.json
  text = obj["text"]
  tid  = int(obj["tid"])
  t = TranslatorFromBitext.query.get(tid)
  return jsonify(mosestranslate.translate_trace(text, t.basename))

@app.route('/actions/search-dictionary', methods=["POST"])
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

#@app.route('/actions/translator-list')
#def translator_list():
#  tlist = []
#  for t in Translator.query.all():
#    tlist.append(t.name)
#
#  return jsonify(status = u"OK", translators = tlist)
