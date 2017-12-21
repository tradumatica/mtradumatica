import train
from celery import Celery
from datetime import datetime
from app import app, db
import shutil
from .models import LanguageModel, TranslatorFromBitext
import time

celery = Celery(app.name, broker = app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(bind=True)
def train_simple_smt(self, c1, c2, translator_id):
  print "Hello"
  tmpdir = train.training_dir_setup(c1.lang, c2.lang, c1.path, c2.path, translator_id)
  proc = train.execute_training(tmpdir)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  #print "Translator tmp dir1: "+tmpdir
  shutil.rmtree(tmpdir, ignore_errors=True) 
  trobjs=[ tr for tr in  TranslatorFromBitext.query.filter(TranslatorFromBitext.task_id ==self.request.id ) ]
  if len(trobjs) == 1:
    tr=trobjs[0]
    tr.mydatefinished=datetime.utcnow()
    tr.exitstatus=proc.returncode
    db.session.commit()
  else:
    print "WARNING: "+str(len(trobjs))+" with same tr_id"

@celery.task(bind=True)
def train_smt(self, l1, l2, bitext, languagemodel, translator_id):
  if l1 == bitext.lang1:
    path1= bitext.get_lang1_path()
    path2= bitext.get_lang2_path()
  else:
    path1= bitext.get_lang2_path()
    path2= bitext.get_lang1_path()
  tmpdir = train.training_dir_setup_translator(l1, l2, path1 , path2, languagemodel.get_blm_path(), languagemodel.get_truecaser_path() , translator_id)
  proc = train.execute_training(tmpdir)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  #print "Translator tmp dir2: "+tmpdir
  shutil.rmtree(tmpdir, ignore_errors=True)
  trobjs=[ tr for tr in  TranslatorFromBitext.query.filter(TranslatorFromBitext.task_id ==self.request.id ) ]
  if len(trobjs) == 1:
    tr=trobjs[0]
    tr.mydatefinished=datetime.utcnow()
    tr.exitstatus=proc.returncode
    db.session.commit()
  else:
    print "WARNING: "+str(len(trobjs))+" with same tr_id"

@celery.task(bind=True)
def tune_smt(self, l1, l2, translator, bitext):
  if l1 == bitext.lang1:
    path1= bitext.get_lang1_path()
    path2= bitext.get_lang2_path()
  else:
    path1= bitext.get_lang2_path()
    path2= bitext.get_lang1_path()
  tmpdir = train.training_dir_setup_tuning(l1, l2, translator.get_path(), path1, path2 )
  proc = train.execute_training(tmpdir)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  shutil.rmtree(tmpdir, ignore_errors=True)
  #print "tmpdir: "+tmpdir

  #Get a translator object configured with DB
  trdb = TranslatorFromBitext.query.get(translator.id)
  trdb.mydateoptfinished=datetime.utcnow()
  db.session.commit()

@celery.task(bind=True)
def train_lm(self, monocorpus, lm_id):
  tmpdir = train.training_dir_setup_lm(monocorpus.lang, monocorpus.path, lm_id)
  proc = train.execute_training(tmpdir)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  #print "LM tmp dir: "+tmpdir
  shutil.rmtree(tmpdir, ignore_errors=True)
  #add finished date to LM object
  lmobjs = [ lm for lm in  LanguageModel.query.filter(LanguageModel.task_id ==self.request.id ) ]
  if len(lmobjs) == 1:
    languagemodel=lmobjs[0]
    languagemodel.mydatefinished=datetime.utcnow()
    languagemodel.exitstatus=proc.returncode
    db.session.commit()
  else:
    print "WARNING: "+str(len(lmobjs))+" with same lm_id"

@celery.task(bind=True)
def translate(self, path, translator, doctype):
  proc   = translate.translate_dir(path, translator, doctype)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  
  tobjs          = [t for t in Translation.query.filter(Translation.task_id == self.request.id)]
  myt            = tobjs[0]
  myt.end        = datetime.utcnow()
  myt.exitstatus = proc.returncode
  db.session.commit()
  
  #shutil.rmtree(tmpdir, ignore_errors=True) # not here
