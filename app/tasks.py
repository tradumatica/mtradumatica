import train
from celery import Celery
from datetime import datetime
from app import app, db
import shutil
from .models import LanguageModel, TranslatorFromBitext, Corpus, Bitext, MonolingualCorpus
import time
import os


celery = Celery(app.name, broker = app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(bind=True)
def train_simple_smt(self, c1_id, c2_id, translator_id):
    c1 = Corpus.query.get(c1_id)
    c2 = Corpus.query.get(c2_id)
    t  = TranslatorFromBitext.query.get(translator_id)
      
    tmpdir = train.training_dir_setup(c1.lang, c2.lang, c1.path, c2.path, t.generated_id)
    proc = train.execute_training(tmpdir)
    self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
    proc.communicate()

    shutil.rmtree(tmpdir, ignore_errors=True)
    
    t.mydatefinished = datetime.utcnow()
    t.exitstatus     = proc.returncode
    db.session.commit()

@celery.task(bind=True)
def train_smt(self, l1, l2, bitext_id, languagemodel_id, translator_id):
  bitext = Bitext.query.get(bitext_id)

  if l1 == bitext.lang1:
    path1= bitext.get_lang1_path()
    path2= bitext.get_lang2_path()
  else:
    path1= bitext.get_lang2_path()
    path2= bitext.get_lang1_path()
    
  languagemodel = LanguageModel.query.get(languagemodel_id)
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
def tune_smt(self, l1, l2, translator_id, bitext_id):
  bitext = Bitext.query.get(bitext_id)
  
  if l1 == bitext.lang1:
    path1= bitext.get_lang1_path()
    path2= bitext.get_lang2_path()
  else:
    path1= bitext.get_lang2_path()
    path2= bitext.get_lang1_path()
    
  translator = TranslatorFromBitext.query.get(translator.id)

  tmpdir = train.training_dir_setup_tuning(l1, l2, translator.get_path(), path1, path2 )
  proc = train.execute_training(tmpdir)
  self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
  proc.communicate()
  shutil.rmtree(tmpdir, ignore_errors=True)
  #print "tmpdir: "+tmpdir

  #Get a translator object configured with DB
  translator.mydateoptfinished=datetime.utcnow()
  db.session.commit()

@celery.task(bind=True)
def train_lm(self, lm_id):
    languagemodel = LanguageModel.query.get(lm_id)
    monocorpus = MonolingualCorpus.query.get(languagemodel.monocorpus_id)
  
    tmpdir = train.training_dir_setup_lm(monocorpus.lang, monocorpus.path, languagemodel.generated_id)
    proc = train.execute_training(tmpdir)
    self.update_state(state="PROGRESS", meta={'proc_id': proc.pid, 'tmpdir': tmpdir})
    proc.communicate()

    #print "LM tmp dir: "+tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)
    #add finished date to LM object

    languagemodel.mydatefinished = datetime.utcnow()
    languagemodel.exitstatus     = proc.returncode
    db.session.commit()

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
