from app import db
from app import app
import train
import datetime
import os
from flask.ext.login import UserMixin
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend

# Many to many relationships

lm_has_corpus = db.Table('lm_has_corpus',
                         db.Column('lm_id', db.Integer, db.ForeignKey('language_model.id')),
                         db.Column('corpus_id', db.Integer, db.ForeignKey('corpus.id')))

tm_has_bitext = db.Table('tm_has_bitext',
                         db.Column('tm_id', db.Integer, db.ForeignKey('translation_model.id')),
                         db.Column('bitext_id', db.Integer, db.ForeignKey('bitext.id')))

class Corpus(db.Model):
  id      = db.Column(db.Integer, primary_key=True)
  name    = db.Column(db.String(100))
  mydate  = db.Column(db.DateTime)
  type    = db.Column(db.String(32))
  lang    = db.Column(db.String(10))
  nlines  = db.Column(db.Integer)
  nwords  = db.Column(db.Integer)
  nchars  = db.Column(db.Integer)
  size    = db.Column(db.Integer)
  path    = db.Column(db.String(256))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  
  def __repr__(self):
    return "<Corpus {0} {1} {2} {3} {4}>".format(self.name, self.nlines, self.nwords, self.nchars, self.lang)

  def __json__(self):
    return {
            'id': self.id,
            'name': self.name,
            'mydate': self.mydate,
	    'type': self.type,
	    'lang': self.lang,
	    'nlines': self.nlines,
	    'nwords': self.nwords,
	    'nchars': self.nchars,
	    'size': self.size,
	    'path': self.path
        }

class LanguageModel(db.Model):
  id      = db.Column(db.Integer, primary_key = True)
  name    = db.Column(db.String(100))
  lang   = db.Column(db.String(10))
  mydate = db.Column(db.DateTime)
  mydatefinished = db.Column(db.DateTime)
  monocorpus_id = db.Column(db.Integer, db.ForeignKey('monolingual_corpus.id'))
  task_id = db.Column(db.String(128))
  path    = db.Column(db.String(256))
  exitstatus = db.Column(db.Integer)
  translatorsfrombitext = db.relationship('TranslatorFromBitext',backref=db.backref('languagemodel', lazy='joined'), lazy='dynamic')
  generated_id = db.Column(db.String(128))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

  def __json__(self):
    return {
            'id': self.id,
            'name': self.name,
            'mydate': self.mydate,
            'lang': self.lang,
            'monocorpus_id': self.monocorpus_id,
            'path': self.path,
            'task_id' : self.task_id,
            'generated_id': self.generated_id
        }
  def get_blm_path(self):
    return os.path.join(self.path,"LM.blm")
  def get_truecaser_path(self):
    return os.path.join(self.path,"corpus."+self.lang+".tcm")

class Bitext(db.Model):
  id    = db.Column(db.Integer, primary_key = True)
  name  = db.Column(db.String(100))
  lang1   = db.Column(db.String(10))
  lang2   = db.Column(db.String(10))
  nlines = db.Column(db.Integer)
  mydate = db.Column(db.DateTime)
  path   = db.Column(db.String(256))
  translatorsfrombitext = db.relationship('TranslatorFromBitext',backref=db.backref('bitext', lazy='joined'), lazy='dynamic')
#  left  = db.Column(db.Integer, db.ForeignKey('corpus.id'))
#  right = db.Column(db.Integer, db.ForeignKey('corpus.id'))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

  def __json__(self):
    return {
            'id': self.id,
            'name': self.name,
            'mydate': self.mydate,
            'lang1': self.lang1,
            'lang2': self.lang2,
            'path': self.path,
            'nlines' : self.nlines
        }
  def get_lang1_path(self):
    return os.path.join(self.path,"0")
  def get_lang2_path(self):
    return os.path.join(self.path,"1")

class MonolingualCorpus(db.Model):
  id    = db.Column(db.Integer, primary_key = True)
  name  = db.Column(db.String(100))
  lang   = db.Column(db.String(10))
  nlines = db.Column(db.Integer)
  mydate = db.Column(db.DateTime)
  path   = db.Column(db.String(256))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

  languagemodels = db.relationship('LanguageModel',backref=db.backref('monocorpus', lazy='joined'), lazy='dynamic')

  def __json__(self):
    return {'id': self.id,
            'name': self.name,
            'mydate': self.mydate,
	    'lang': self.lang,
	    'nlines': self.nlines,
            'path': self.path}

#TODO: create class AddTMXBitext
class AddCorpusBitext(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  position =  db.Column(db.Integer)
  bitext = db.Column(db.Integer, db.ForeignKey('bitext.id'))
  corpus1 = db.Column(db.Integer, db.ForeignKey('corpus.id'))
  corpus2 = db.Column(db.Integer, db.ForeignKey('corpus.id'))

class AddCorpusMonoCorpus(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  position =  db.Column(db.Integer)
  monocorpus = db.Column(db.Integer, db.ForeignKey('monolingual_corpus.id'))
  corpus = db.Column(db.Integer, db.ForeignKey('corpus.id'))

class TranslatorFromBitext(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name              = db.Column(db.String(100))
  lang1             = db.Column(db.String(10))
  lang2             = db.Column(db.String(10))
  mydate            = db.Column(db.DateTime)
  mydatefinished    = db.Column(db.DateTime)
  mydateopt         = db.Column(db.DateTime)
  mydateoptfinished = db.Column(db.DateTime)
  bitext_id         = db.Column(db.Integer, db.ForeignKey('bitext.id'))
  languagemodel_id  = db.Column(db.Integer, db.ForeignKey('language_model.id'))
  task_id           = db.Column(db.String(128))
  task_opt_id       = db.Column(db.String(128))
  generated_id      = db.Column(db.String(128))
  basename          = db.Column(db.String(256))
  exitstatus        = db.Column(db.Integer)
  moses_served      = db.Column(db.Boolean, default=False)
  moses_served_port = db.Column(db.Integer)
  user_id           = db.Column(db.Integer, db.ForeignKey('users.id'))

  def get_path(self):
    result = []
    for i in self.basename.split(";;;;"):
      result.append(train.build_translator_path(i))
    return result

class Translation(db.Model):
  id          = db.Column(db.Integer, primary_key = True)
  t_name      = db.Column(db.String(100))
  f_name      = db.Column(db.String(256))
  lang1       = db.Column(db.String(10))
  lang2       = db.Column(db.String(10))
  start       = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  end         = db.Column(db.DateTime)            
  doctype     = db.Column(db.String(10))
  mimetype    = db.Column(db.String(64))
  size        = db.Column(db.Integer)
  exit_status = db.Column(db.Integer)
  task_id     = db.Column(db.String(128))
  path        = db.Column(db.String(256))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#This class is never used
class TranslationModel(db.Model):
  id      = db.Column(db.Integer, primary_key = True)
  name    = db.Column(db.String(100))
  corpora = db.relationship('Bitext', secondary = tm_has_bitext)
  path    = db.Column(db.String(256))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


#This class is never used
class SMT(db.Model):
  id   = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(100))
  lm   = db.Column(db.Integer, db.ForeignKey('language_model.id'))
  tm   = db.Column(db.Integer, db.ForeignKey('translation_model.id'))

#This class will be deprecated soon
class Translator(db.Model):
  id      = db.Column(db.Integer, primary_key = True)
  name    = db.Column(db.String(100))
  task_id = db.Column(db.String(128))
  path    = db.Column(db.String(1024))
  start   = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  sl      = db.Column(db.String(10))
  tl      = db.Column(db.String(10))
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class User(UserMixin, db.Model):
  __tablename__   = 'users'
  id              = db.Column(db.Integer, primary_key=True)
  username        = db.Column(db.String(250))
  social_id       = db.Column(db.String(250))
  email           = db.Column(db.String(60), unique=True)
  admin           = db.Column(db.Boolean, default=False)
  corpora         = db.relationship("Corpus")
  language_models = db.relationship("LanguageModel")
  bitexts         = db.relationship("Bitext")
  mono_corpora    = db.relationship("MonolingualCorpus")
  tfbitexts       = db.relationship("TranslatorFromBitext")
  translation     = db.relationship("Translation")
  translators     = db.relationship("Translator")

class OAuth(OAuthConsumerMixin, db.Model):
  __tablename__ = "flask_dance_oauth"
  user_id = db.Column(db.Integer, db.ForeignKey(User.id))
  user    = db.relationship("User")  
