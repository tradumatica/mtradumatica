import subprocess 
import regex
import tempfile
import os
import codecs
from app import app

#tempfile.tempdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/tmp"

tempfile.tempdir = app.config['TMP_FOLDER']


nl       = regex.compile(r"[\n]", regex.MULTILINE)
doublenl = regex.compile(r"[\n][\n]", regex.MULTILINE)
vt       = regex.compile(r"\v")
splitter = regex.compile(r"(?<!\w\.\w.)(?<![[:upper:]][[:lower:]]\.)(?<=\.|\?)[ \\t\\f\\v]")
blanknl  = regex.compile(r"[ ]+\n", regex.MULTILINE)
nlblank  = regex.compile(r"\n[ ]+", regex.MULTILINE)

from app import app
qlm = app.config['QUERY_LM_PROGRAM']
qtm = app.config['QUERY_TM_PROGRAM']

def query_lm(text, model):
  text = nl.sub("\n\n", text)  
  text = splitter.sub("\n", text)
  
  input = tempfile.NamedTemporaryFile(delete = False)
  input.write(text.encode("utf8"))
  input.write("\n".encode("utf-8"))
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
  text = text.replace("\"", "");
  text = text.replace("\n", " ");
  
  output= tempfile.NamedTemporaryFile(delete = False)
  output.close()
  query_command = '{0} {1} "{2}" 1000 >{3}'.format(qtm, model, text, output.name)
  proc = subprocess.Popen(query_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  
  list = []
  with codecs.open(output.name, "r", "utf-8") as f:
    for i in f:
      list.append(i)
  
  os.unlink(output.name);
  
  return list
