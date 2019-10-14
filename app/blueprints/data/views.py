from app import app
from app.utils import utils, user_utils, metrics
from app import db
from app.models import MonolingualCorpus, Bitext, Corpus, AddCorpusBitext, AddCorpusMonoCorpus, TranslatorFromBitext

from flask import Blueprint, render_template, abort, request, jsonify, Response
from flask_login import login_required, current_user
from flask_babel import _
from werkzeug import secure_filename
from random import randint
from datetime import datetime

import magic
import os
import shutil

USER_LOGIN_ENABLED = user_utils.isUserLoginEnabled()

data_blueprint = Blueprint('data', __name__, template_folder='templates')

@data_blueprint.route('/files', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def files():
  return render_template("files.html", title = _("File manager"),
                         user = user_utils.get_user())

@data_blueprint.route('/bitexts', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitexts():
  data = Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).all()
  return render_template("bitexts.html", title = _("Bitext manager"), data = data,
                         user = user_utils.get_user())

@data_blueprint.route('/monolingual_corpora', methods=["GET","POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
def monolingual_corpora():
  return render_template("monolingual-corpora.html", title = _("Monolingual corpora"),
                         user = user_utils.get_user())

@data_blueprint.route('/actions/bitext-create/<string:parname>/<string:language1>/<string:language2>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitext_create(parname,language1,language2):
  #TODO: check existing bitext with the same name?
  language1,language2=utils.sort_language_pair(language1,language2)
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
             mydate  = datetime.utcnow(), path= dirname, user_id = user_utils.get_uid())

  fd0=open(b.get_lang1_path(),'w')
  fd0.close()
  fd1=open(b.get_lang2_path(),'w')
  fd1.close()

  db.session.add(b)
  db.session.commit()

  return jsonify(status = "OK")

@data_blueprint.route('/actions/monolingualcorpus-create/<string:parname>/<string:language1>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
                        path = filename, user_id = user_utils.get_uid())
  db.session.add(m)
  db.session.commit()

  return jsonify(status = "OK")

@data_blueprint.route('/actions/monolingualcorpus-list', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    icons      = '<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="addtomonocorpus-{0}-{1}" class="glyphicon glyphicon-plus-sign" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang, c.nlines, c.mydate.strftime(date_fmt) ,  icons.format(c.id,c.lang)]
            for c in MonolingualCorpus.query.filter(MonolingualCorpus.user_id == user_utils.get_uid()).filter(MonolingualCorpus.name.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == user_utils.get_uid()).count(),
                   recordsFiltered = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == user_utils.get_uid()).filter(MonolingualCorpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@data_blueprint.route('/actions/bitext-list', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    icons      = '<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="addtobitext-{0}-{1}-{2}" class="glyphicon glyphicon-plus-sign" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang1 +"-"+ c.lang2, c.nlines, c.mydate.strftime(date_fmt) ,  icons.format(c.id,c.lang1,c.lang2)]
            for c in Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).filter(Bitext.name.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).count(),
                   recordsFiltered = Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).filter(Bitext.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@data_blueprint.route('/actions/file-list', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    icons      = '<span id="peek-{0}" class="glyphicon glyphicon-eye-open" aria-hidden="true"></span> <span id="download-{0}" class="glyphicon glyphicon-download-alt" aria-hidden="true"></span>'

    data = [[checkbox.format(c.id),
             c.name, c.lang, c.nlines, "{} ({})".format(c.nwords, c.uwords), c.nchars,
             c.mydate.strftime(date_fmt), icons.format(c.id)]
            for c in Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).filter(Corpus.name.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
#             for c in Corpus.query.filter(Corpus.name.like(search_str)).order_by(order_str)][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).count(),
                   recordsFiltered = Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).filter(Corpus.name.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@data_blueprint.route('/actions/file-upload', methods=["POST"])
@utils.condec(login_required, USER_LOGIN_ENABLED)
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
      uw = metrics.count_unique_words(i)
      c = Corpus(name = basename, mydate = datetime.utcnow(),
               lang = lang if mimetype[0:4] == "text" else '<binary>', nlines = nl, nwords = nw,
               nchars = nc, size = sz, path = i,
               type = mimetype, user_id = user_utils.get_uid(), uwords = uw)

      db.session.add(c)
    db.session.commit()
    os.unlink(filename)
  else:
    uw = metrics.count_unique_words(filename)    
    c = Corpus(name = basename, mydate = datetime.utcnow(),
               lang = lang if mimetype[0:4] == "text" else '<binary>', nlines = nl, nwords = nw,
               nchars = nc, size = sz, path = filename,
               type = mimetype, user_id = user_utils.get_uid(), uwords = uw)

    db.session.add(c)
    db.session.commit()

  return jsonify(status = "OK")

@data_blueprint.route('/actions/file-delete/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@data_blueprint.route('/actions/bitext-delete/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitext_delete(id):
  bitext = Bitext.query.get(id)
  if bitext is None:
    abort(401)
    return
  try:
    shutil.rmtree(bitext.path)
  except OSError as e:
    print(e)

  db.session.delete(bitext)
  db.session.commit()
  return jsonify(status = "OK")

@data_blueprint.route('/actions/monolingualcorpus-delete/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def monolingualcorpus_delete(id):
  monocorpus = MonolingualCorpus.query.get(id)
  if monocorpus is None:
    abort(401)
    return
  try:
    os.unlink(monocorpus.path)
  except OSError as e:
    print(e)

  db.session.delete(monocorpus)
  db.session.commit()
  return jsonify(status = "OK")

@data_blueprint.route('/actions/bitext-add-files/<int:id>/<int:idfile1>/<int:idfile2>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitext_add_files(id,idfile1, idfile2):
  #DEBUG
  print("Appending files to bitext {0}: {1} and {2}".format(id,idfile1, idfile2))
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


@data_blueprint.route('/actions/monolingualcorpus-add-files/<int:id>/<int:idfile1>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@data_blueprint.route('/actions/file-plainlist')
@data_blueprint.route('/actions/file-plainlist/<string:language>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def file_plain_list(language=None):
  files=[]
  if language != None:
    files = Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).filter(Corpus.lang == language)
  else:
    files = Corpus.query.filter(Corpus.user_id == user_utils.get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])

@data_blueprint.route('/actions/bitext-plainlist')
@data_blueprint.route('/actions/bitext-plainlist/<string:language1>/<string:language2>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitext_plain_list(language1=None, language2=None):
  files=[]
  if language1 != None and language2 != None:
    #sort languages
    language1,language2=utils.sort_language_pair(language1,language2)
    files= Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  else:
    files= Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])

@data_blueprint.route('/actions/bitext-plainlist/<int:trid>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def bitext_plain_list_for_translator(trid):
  files=[]
  tr = TranslatorFromBitext.query.get(trid)
  if tr != None:
    #sort languages
    language1,language2=utils.sort_language_pair(tr.lang1,tr.lang2)
    files= Bitext.query.filter(Bitext.user_id == user_utils.get_uid()).filter(Bitext.lang1 == language1).filter(Bitext.lang2 == language2)
  return jsonify(data=[f.__json__() for f in files])

@data_blueprint.route('/actions/monolingualcorpus-plainlist')
@data_blueprint.route('/actions/monolingualcorpus-plainlist/<string:language>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def monolingualCorpus_plain_list(language=None):
  files=[]
  if language != None:
    files = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == user_utils.get_uid()).filter(MonolingualCorpus.lang == language)
  else:
    files = MonolingualCorpus.query.filter(MonolingualCorpus.user_id == user_utils.get_uid()).all()
  return jsonify(data=[f.__json__() for f in files])


@data_blueprint.route('/actions/file-download/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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

@data_blueprint.route('/actions/file-peek/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def file_peek(id):
  corpus = Corpus.query.get(id)

  f = open(corpus.path, "r")
  data = f.read(1024*20)
  f.close()

  result = []
  if data:
    result = data.split("\n")[0:20]

  return jsonify(lines = result, filename=corpus.name)

@data_blueprint.route('/actions/file-setlang/<int:id>/<string:code>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def file_setlang(id, code):
  corpus = Corpus.query.get(id)
  corpus.lang = code
  db.session.commit()

  return jsonify(status = "OK")

@data_blueprint.route('/actions/monolingualcorpus-peek/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
def monolingualcorpus_peek(id):
  corpus = MonolingualCorpus.query.get(id)

  f = open(corpus.path, "r")
  data = f.read(1024*20)
  f.close()

  result = []
  if data:
    result = data.split("\n")[0:20]

  return jsonify(lines = result, filename=corpus.name)

@data_blueprint.route('/actions/bitext-peek/<int:id>')
@utils.condec(login_required, USER_LOGIN_ENABLED)
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