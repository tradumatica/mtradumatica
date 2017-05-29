import subprocess 
import regex
import tempfile
import os
import codecs

tempfile.tempdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/tmp"


nl       = regex.compile(ur"[\n]", regex.MULTILINE)
doublenl = regex.compile(ur"[\n][\n]", regex.MULTILINE)
vt       = regex.compile(ur"\v")
splitter = regex.compile(ur"(?<!\w\.\w.)(?<![[:upper:]][[:lower:]]\.)(?<=\.|\?)[ \\t\\f\\v]")
blanknl  = regex.compile(ur"[ ]+\n", regex.MULTILINE)
nlblank  = regex.compile(ur"\n[ ]+", regex.MULTILINE)

from app import app
qlm = app.config['QUERY_LM_PROGRAM']
qtm = app.config['QUERY_TM_PROGRAM']

def query_lm(text, model):
  text = nl.sub(u"\n\n", text)  
  text = splitter.sub(u"\n", text)
  
  input = tempfile.NamedTemporaryFile(delete = False)
  input.write(text.encode("utf8"))
  input.write("\n")
  input.close()
  
  output= tempfile.NamedTemporaryFile(delete = False)
  output.close()
  query_command = "{0} {1} <{2} >{3}".format(qlm, model, input.name, output.name)
  proc = subprocess.Popen(query_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  
  list = []
  with codecs.open(output.name, "r", "utf-8") as f:
    for i in f:
      list.append(i)
  
  os.unlink(input.name);
  os.unlink(output.name);
  
  return list

def query_tm(text, model):
  text = nl.sub(u"\n\n", text)  
  text = splitter.sub(u"\n", text)
  
  input = tempfile.NamedTemporaryFile(delete = False)
  input.write(text.encode("utf8"))
  input.close()
  
  output= tempfile.NamedTemporaryFile(delete = False)
  output.close()
  query_command = "{0} -a -t {1} <{2} >{3}".format(qtm, model, input.name, output.name)
  proc = subprocess.Popen(query_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  
  list = []
  with codecs.open(output.name, "r", "utf-8") as f:
    for i in f:
      list.append(i)
  
  os.unlink(input.name);
  os.unlink(output.name);
  
  return list
