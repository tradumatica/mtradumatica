import os
import tempfile
import subprocess
import signal
import string
import random
import shutil
import sys
from app import app,db

#tempfile.tempdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/tmp"
tempfile.tempdir = app.config['TMP_FOLDER']

def get_makefile_tuning(l1,l2, translatorpath):
  rootdir  = app.config['BASEDIR'] or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

  makefile = """
L1               := {0}
L2               := {1}
PREFIX           := {2}/venv/local
LM_ORDER         := 3
CORES            := $(shell getconf _NPROCESSORS_ONLN)
EFFECTIVE_CORES  := $(shell echo $$(( $(CORES) / 2 )))
current_dir      := $(shell pwd)

ifeq ($(EFFECTIVE_CORES),0)
EFFECTIVE_CORES:=1
endif

CUR_TMP_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

export PATH            := $(PREFIX)/bin:$(PREFIX)/scripts/training:$(PREFIX)/scripts/tokenizer:$(PREFIX)/scripts/recaser:$(PATH)
export LD_LIBRARY_PATH := $(PREFIX)/lib
export TMPDIR := {2}/tmp

objs = ./tuning/moses.ini {3}/moses.tuned.ini

all: $(objs)

{3}/moses.tuned.ini: ./tuning/moses.ini
	cat ./tuning/moses.ini | sed "s:path=$(CUR_TMP_DIR)/:path=:" > {3}/moses.tuned.ini

./tuning/moses.ini: moses.ini dev.$(L1).tok.low dev.$(L2).tok.low moses.absolute.ini
	mkdir -p ./tuning
	mert-moses.pl $(CUR_TMP_DIR)/dev.$(L1).tok.low $(CUR_TMP_DIR)/dev.$(L2).tok.low $(PREFIX)/bin/moses $(CUR_TMP_DIR)/moses.absolute.ini  --working-dir $(CUR_TMP_DIR)/tuning  --batch-mira --return-best-dev --decoder-flags="-threads $(EFFECTIVE_CORES)" --no-filter-phrase-table -maximum-iterations 20

moses.absolute.ini: moses.ini
	cat moses.ini  | sed "s:path=:path=$(CUR_TMP_DIR)/:" > moses.absolute.ini

dev.$(L1).tok.low: dev.2000 sl.tcm
	cut -f1 dev.2000 | tokenizer.perl -threads $(EFFECTIVE_CORES) -l $(L1) | truecase.perl --model sl.tcm >$@

dev.$(L2).tok.low: dev.2000 tl.tcm
	cut -f2 dev.2000 | tokenizer.perl -threads $(EFFECTIVE_CORES) -l $(L2) | truecase.perl --model tl.tcm >$@
	
dev.2000: dev.$(L1) dev.$(L2)
	paste dev.$(L1) dev.$(L2) | shuf -n 2000 >$@

clean:
	rm -Rf $(objs)
"""
  return makefile.format(l1, l2, rootdir, translatorpath)

def get_makefile_lm(l1, destprefix):
  rootdir  = app.config['BASEDIR'] or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

  makefile = """
L1               := {0}
L2               := {1}
PREFIX           := {2}/venv/local
LM_ORDER         := 3
CORES            := $(shell getconf _NPROCESSORS_ONLN)
EFFECTIVE_CORES  := $(shell echo $$(( $(CORES) / 2 )))
current_dir      := $(shell pwd)

ifeq ($(EFFECTIVE_CORES),0)
EFFECTIVE_CORES:=1
endif

export PATH            := $(PREFIX)/bin:$(PREFIX)/scripts/training:$(PREFIX)/scripts/tokenizer:$(PREFIX)/scripts/recaser:$(PATH)
export LD_LIBRARY_PATH := $(PREFIX)/lib


objs = LM.arpa \
 LM.blm \
 corpus.$(L2).tcm \
 ../../lms/{3}-$(L2)

all: $(objs)

../../lms/{3}-$(L2): LM.blm LM.arpa corpus.$(L2).tcm
	mkdir -p ../../lms/{3}-$(L2)
	ln LM.blm      ../../lms/{3}-$(L2)/LM.blm
	ln LM.arpa ../../lms/{3}-$(L2)/LM.arpa
	ln corpus.$(L2).tcm                   ../../lms/{3}-$(L2)/corpus.$(L2).tcm

LM.blm: LM.arpa
	build_binary $< $@

LM.arpa: corpus.$(L2).true
	lmplz --discount_fallback -o $(LM_ORDER) -S 80% -T . <$< >$@

corpus.$(L2).true: corpus.$(L2).tcm corpus.$(L2).tok
	truecase.perl --model $< <$(word 2,$^) >$@

corpus.$(L2).tcm: corpus.$(L2).tok
	train-truecaser.perl --model $@ --corpus $<

corpus.$(L2).tok: corpus.$(L2)
	tokenizer.perl -threads $(EFFECTIVE_CORES) -l $(L2) <$< >$@

clean:
	rm -Rf $(objs)
"""

  return makefile.format("l1", l1, rootdir, destprefix)

def get_makefile(l1, l2, destprefix, trainLM=True):
  rootdir  = app.config['BASEDIR'] or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
  makefile = """
L1               := {0}
L2               := {1}
PREFIX           := {2}/venv/local
LM_ORDER         := 3
EXTERNAL_BIN_DIR := $(PREFIX)/bin
GIZA_ALIGN       := grow-diag-final-and
GIZA_REORDERING  := msd-bidirectional-fe   # msd-bidirectional-fe,phrase-msd-bidirectional-fe,hier-mslr-bidirectional-fe
CORES            := $(shell getconf _NPROCESSORS_ONLN)
EFFECTIVE_CORES  := $(shell echo $$(( $(CORES) / 2 )))
current_dir      := $(shell pwd)

ifeq ($(EFFECTIVE_CORES),0)
EFFECTIVE_CORES:=1
endif

export PATH            := $(PREFIX)/bin:$(PREFIX)/scripts/training:$(PREFIX)/scripts/tokenizer:$(PREFIX)/scripts/recaser:$(PATH)
export LD_LIBRARY_PATH := $(PREFIX)/lib

define MOSES_INI
#########################
### MOSES CONFIG FILE ###
#########################

[input-factors]
0

# mapping steps
[mapping]
0 T 0

[distortion-limit]
6

# feature functions
[feature]
UnknownWordPenalty
WordPenalty
PhrasePenalty
PhraseDictionaryCompact name=TranslationModel0 num-features=4 path=phrase-table.minphr input-factor=0 output-factor=0
LexicalReordering name=LexicalReordering0 num-features=6 type=wbe-msd-bidirectional-fe-allff input-factor=0 output-factor=0 path=reordering-table
Distortion
KENLM lazyken=0 name=LM0 factor=0 path=LM.blm order=$(LM_ORDER)

# dense weights for feature functions
[weight]
# The default weights are NOT optimized for translation quality. You MUST tune the weights.
# Documentation for tuning is here: http://www.statmt.org/moses/?n=FactoredTraining.Tuning
UnknownWordPenalty0= 1
WordPenalty0= -1
PhrasePenalty0= 0.2
TranslationModel0= 0.2 0.2 0.2 0.2
LexicalReordering0= 0.3 0.3 0.3 0.3 0.3 0.3
Distortion0= 0.3
LM0= 0.5
endef

export MOSES_INI

targets = corpus.$(L1).tok corpus.$(L2).tok \
       corpus.$(L1).tcm corpus.$(L2).tcm \
       corpus.$(L1).true corpus.$(L2).true \
       corpus.$(L1).clean corpus.$(L2).clean \
       corpus.clean.$(L1) corpus.clean.$(L2) \
       LM.blm \
       train.ok phrase-table.minphr reordering-table.minlexr \
       ../../translators/{3}-$(L1)-$(L2)

objs = $(targets) LM.arpa

all: $(targets)

../../translators/{3}-$(L1)-$(L2): phrase-table.minphr reordering-table.minlexr LM.blm corpus.$(L1).tcm
	mkdir ../../translators/{3}-$(L1)-$(L2)
	ln phrase-table.minphr      ../../translators/{3}-$(L1)-$(L2)/phrase-table.minphr
	ln reordering-table.minlexr ../../translators/{3}-$(L1)-$(L2)/reordering-table.minlexr
	ln LM.blm                   ../../translators/{3}-$(L1)-$(L2)/LM.blm
	ln corpus.$(L1).tcm         ../../translators/{3}-$(L1)-$(L2)/sl.tcm
	ln corpus.$(L2).tcm         ../../translators/{3}-$(L1)-$(L2)/tl.tcm
	ln model/lex.e2f            ../../translators/{3}-$(L1)-$(L2)/lex.e2f
	ln model/lex.f2e            ../../translators/{3}-$(L1)-$(L2)/lex.f2e
	@echo "$$MOSES_INI"        >../../translators/{3}-$(L1)-$(L2)/moses.ini

phrase-table.minphr: model/phrase-table.gz
	processPhraseTableMin -in $< -out phrase-table -nscores 4 -threads $(EFFECTIVE_CORES)

reordering-table.minlexr: model/reordering-table.wbe-msd-bidirectional-fe.gz
	processLexicalTableMin -in $< -out reordering-table -threads $(EFFECTIVE_CORES)

model/phrase-table.gz: train.ok
model/reordering-table.wbe-msd-bidirectional-fe.gz: train.ok

train.ok: corpus.clean.$(L1) corpus.clean.$(L2) LM.blm
	train-model.perl -root-dir . -corpus corpus.clean -f $(L1) -e $(L2) \
	  -alignment $(GIZA_ALIGN) -reordering $(GIZA_REORDERING) \
   	  -lm 0:$(LM_ORDER):$(current_dir)/LM.blm:8 \
	  -external-bin-dir $(EXTERNAL_BIN_DIR) \
	  -mgiza -mgiza-cpus=$(EFFECTIVE_CORES) -parallel && touch $@

corpus.clean.$(L1): corpus.$(L1).clean
	ln -s $< $@

corpus.clean.$(L2): corpus.$(L2).clean
	ln -s $< $@

corpus.$(L1).clean: corpus.$(L1).true corpus.$(L2).true
	ln -s $< tmp.$(L1)
	ln -s $(word 2,$^) tmp.$(L2)
	clean-corpus-n.perl tmp $(L1) $(L2) clean 1 80
	rm tmp.$(L1) tmp.$(L2)
	mv clean.$(L1) $@

corpus.$(L2).clean: corpus.$(L1).clean
	mv clean.$(L2) $@

corpus.$(L1).true: corpus.$(L1).tcm corpus.$(L1).tok
	truecase.perl --model $< <$(word 2,$^) >$@

corpus.$(L2).true: corpus.$(L2).tcm corpus.$(L2).tok
	truecase.perl --model $< <$(word 2,$^) >$@

corpus.$(L1).tcm: corpus.$(L1).tok
	train-truecaser.perl --model $@ --corpus $<

corpus.$(L1).tok: corpus.$(L1)
	tokenizer.perl -threads $(EFFECTIVE_CORES) -l $(L1) <$< >$@

corpus.$(L2).tok: corpus.$(L2)
	tokenizer.perl -threads $(EFFECTIVE_CORES) -l $(L2) <$< >$@

clean:
	rm -Rf $(objs) corpus model giza.$(L1)-$(L2) giza.$(L2)-$(L1)
"""

  makefileTrainLM="""
corpus.$(L2).tcm: corpus.$(L2).tok
	train-truecaser.perl --model $@ --corpus $<

LM.blm: LM.arpa
	build_binary $< $@

LM.arpa: corpus.$(L2).true
	lmplz --discount_fallback -o $(LM_ORDER) -S 80% -T . <$< >$@

"""

  if trainLM:
    makefile+=makefileTrainLM

  return makefile.format(l1, l2, rootdir, destprefix)

## Set-up training of translation model ##
def training_dir_setup_translator(l1, l2, c1, c2, blm , tl_truecaser , destprefix):
  mydir = tempfile.mkdtemp(suffix="-{0}-{1}".format(l1, l2))

  with open(mydir+"/Makefile", "w") as f:
    f.write(get_makefile(l1, l2, destprefix, trainLM=False))

  os.link(c1, mydir + "/corpus." + l1)
  os.link(c2, mydir + "/corpus." + l2)
  os.link(blm, mydir + "/LM.blm")
  os.link(tl_truecaser, mydir + "/corpus." + l2+".tcm")

  return mydir

#This funcion will be removed soon
def training_dir_setup(l1, l2, c1, c2, destprefix):
  mydir = tempfile.mkdtemp(suffix="-{0}-{1}".format(l1, l2))

  with open(mydir+"/Makefile", "w") as f:
    f.write(get_makefile(l1, l2, destprefix))

  os.link(c1, mydir + "/corpus." + l1)
  os.link(c2, mydir + "/corpus." + l2)

  return mydir


## Set-up training of language model ##
def training_dir_setup_lm( l1,c1, destprefix):
  mydir = tempfile.mkdtemp(suffix="-{0}".format(l1))
  with open(mydir+"/Makefile", "w") as f:
    f.write(get_makefile_lm(l1, destprefix))

  os.symlink(c1, mydir + "/corpus." + l1)
  return mydir


## Set-up tuning ##
def training_dir_setup_tuning( l1,l2, translatorpath, devset1, devset2):
  mydir = tempfile.mkdtemp(suffix="-{0}-{1}".format(l1,l2))
  with open(mydir+"/Makefile", "w") as f:
    f.write(get_makefile_tuning(l1, l2, translatorpath))
  os.symlink(devset1, mydir + "/dev." + l1)
  os.symlink(devset2, mydir + "/dev." + l2)
  os.symlink(os.path.join(translatorpath,"LM.blm") , mydir + "/LM.blm")
  os.symlink(os.path.join(translatorpath,"moses.ini") , mydir + "/moses.ini")
  os.symlink(os.path.join(translatorpath,"phrase-table.minphr") , mydir + "/phrase-table.minphr")
  os.symlink(os.path.join(translatorpath,"reordering-table.minlexr") , mydir + "/reordering-table.minlexr")
  os.symlink(os.path.join(translatorpath,"sl.tcm") , mydir + "/sl.tcm")
  os.symlink(os.path.join(translatorpath,"tl.tcm") , mydir + "/tl.tcm")
  
  return mydir

def execute_training(dir):
  DEVNULL = open(os.devnull, 'w')
  err=open(dir+"/log.err","w")
  out=open(dir+"/log.out","w")
  return subprocess.Popen("make -j -C " + dir, shell = True, stdout=out, stderr=err, preexec_fn=os.setsid, close_fds=True)

def kill_execution(pid, dir):
  os.killpg(pid, signal.SIGTERM)
  shutil.rmtree(dir, ignore_errors=True)

def is_proc_running(pid):
  try:
    os.kill(pid, 0)
  except OSError:
    return False
  else:
    return True

def id_generator_unsafe(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

def id_generator(l1,l2):
  id=id_generator_unsafe()
  dirname = build_translator_path(build_translator_basename(id,l1,l2))
  while os.path.exists(dirname):
    id=id_generator_unsafe()
    dirname = build_translator_path(build_translator_basename(id,l1,l2))
  return id

def lm_id_generator(l2):
  id=id_generator_unsafe()
  dirname = build_lm_path(id, l2)
  while os.path.exists(dirname):
    id=id_generator_unsafe()
    dirname = build_lm_path(id, l2)
  return id

def build_translator_basename(id,l1,l2):
  return "{0}-{1}-{2}".format(id,l1,l2)

def build_translator_path(basename):
  return os.path.join(app.config['TRANSLATORS_FOLDER'],basename)

def build_lm_path(id,l2):
  return os.path.join(app.config['LMS_FOLDER'],"{0}-{1}".format(id,l2))
