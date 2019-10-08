import subprocess 
import regex
import tempfile
import os
import codecs
import shutil
from app import app


#tempfile.tempdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/tmp"
tempfile.tempdir = app.config['TMP_FOLDER']
doctypes = ["txt", "odt", "ods", "odp", "docx", "xlsx", "pptx", "html", "xml"]

nl       = regex.compile(ur"[\n]", regex.MULTILINE)
doublenl = regex.compile(ur"[\n][\n]", regex.MULTILINE)
vt       = regex.compile(ur"\v")
splitter = regex.compile(ur"(?<!\w\.\w.)(?<![[:upper:]][[:lower:]]\.)(?<=\.|\?)[ \\t\\f\\v]")
blanknl  = regex.compile(ur"[ ]+\n", regex.MULTILINE)
nlblank  = regex.compile(ur"\n[ ]+", regex.MULTILINE)

from app import app
tp       = app.config['TRANSLATION_PROGRAM']
rp       = app.config['REBUNDLE_PROGRAM']
tp_trace = app.config['TRANSLATION_PROGRAM_TRACE']
tmx_unf  = app.config['TMX_UNFORMAT_SCRIPT']
tmx_ref  = app.config['TMX_REFORMAT_SCRIPT']

def translate(text, translator, doctype="txt"):
  text = nl.sub(u"\n\n", text)  
  text = splitter.sub(u"\n", text)
  
  input = tempfile.NamedTemporaryFile(delete = False)
  input.write(text.encode("utf8"))
  input.close()
  
  output= tempfile.NamedTemporaryFile(delete = False)
  output.close()
  translation_command = '{0} -f {1} "{2}" {3} {4}'.format(tp, doctype, translator, input.name, output.name)
  proc = subprocess.Popen(translation_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  
  list = []
  with codecs.open(output.name, "r", "utf-8") as f:
    for i in f:
      list.append(i)
  
  result = u"".join(list)

  result = doublenl.sub(u"\v", result)
  result = nl.sub(u" ", result)
  result = vt.sub(u"\n", result)
  result = blanknl.sub(u"\n", result)
  result = nlblank.sub(u"\n", result)
  
  os.unlink(input.name);
  os.unlink(output.name);
  
  return result


def translate_document(document_name, translator, doctype="txt"):
  output = tempfile.NamedTemporaryFile(delete = False)
  output.close()
  translation_command = '{0} -f {1} "{2}" {3} {4}'.format(tp, doctype, translator, document_name, output.name)
  proc = subprocess.Popen(translation_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  return output.name

def translate_document_tmx(document_name, translator, doctype, filename, lang1, lang2):
  # Translate with -t
  output = tempfile.NamedTemporaryFile(delete = False)
  output.close()
  translation_command = '{0} -t -f {1} "{2}" {3} {4}'.format(tp, doctype, translator, document_name, output.name)
  proc = subprocess.Popen(translation_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  
  # Rebundle tar to zip using the rebundle.sh script
  output2 = tempfile.NamedTemporaryFile(delete = False, suffix=".zip")
  output2.close()
  rebundle_command = "{} {} {} {}-{} {} {}".format(rp, filename, doctype, lang1, lang2, output.name, output2.name)
  proc = subprocess.Popen(rebundle_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate()
  
  os.unlink(output.name)
  
  return output2.name

def translate_tmx(document_name, translator, lang1, lang2):
  output = tempfile.NamedTemporaryFile(delete=False)
  output.close()
  translation_command = "python3 {} {} {} <{} | {} -f html-noent {} | python3 {} >{}".format(tmx_unf, lang1, lang2, document_name, tp, translator, tmx_ref, output.name)
  proc = subprocess.Popen(translation_command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
  return output.name

def translate_dir(temporary_dir, translator, doctype):
  #f = open("/opt/status", "a+")
  #f.write("Esto es una verguenza")
  #f.close()
  source_file = os.path.join(temporary_dir, "source")
  target_file = os.path.join(temporary_dir, "target")
    
  translation_command = '{0} -f {1} "{2}" {3} {4}'.format(tp, doctype, translator, source_file, target_file)
  print(translation_command)
  return subprocess.Popen(translation_command, shell = True, preexec_fn = os.setsid, close_fds = True)
#  proc.communicate();

def translate_dir_setup(obj):
  mydir = tempfile.mkdtemp()
  source_file = os.path.join(mydir, "source")
  
  with open(source_file, "w+b") as output:
    output.write(obj.read())
  
  return mydir

def translate_trace(text, translator):
  text = nl.sub(u"\n\n", text)  
  text = splitter.sub(u"\n", text)
  
  input = tempfile.TemporaryFile()
  input.write(text.encode("utf8"))
  input.seek(0, 0)
  
  tempdir = tempfile.mkdtemp()

  proc = subprocess.Popen([tp_trace, translator, tempdir], stdin = input)
  proc.communicate()
  
  input.close()
  
  trace = {}

  with codecs.open(os.path.join(tempdir,"output"), "r", "utf-8") as f:
    output = f.read()
    output = doublenl.sub(u"\v", output)
    output = nl.sub(u" ", output)
    output = vt.sub(u"\n", output)
    output = blanknl.sub(u"\n", output)
    output = nlblank.sub(u"\n", output)
    trace["output"] = output
  
  with open(os.path.join(tempdir,"input"), "r") as f:
    trace["input"] = f.read()

  with open(os.path.join(tempdir,"input.tok"), "r") as f:
    trace["input_tok"] = f.read().strip()

  with open(os.path.join(tempdir,"input.tru"), "r") as f:
    trace["input_tru"] = f.read().strip()

  with open(os.path.join(tempdir,"translation-details.txt"), "r") as f:
    trace["details"] = f.read().strip()

  with open(os.path.join(tempdir,"alignments.txt"), "r") as f:
    trace["align"] = f.read().strip()

  with open(os.path.join(tempdir,"unknown-words.txt"), "r") as f:
    trace["unknown"] = f.read().strip()

  with open(os.path.join(tempdir,"nbest-list.txt"), "r") as f:
    trace["nbest"] = f.read().strip()
 
  with open(os.path.join(tempdir,"output.tru"), "r") as f:
    trace["output_tru"] = f.read().strip()

  with open(os.path.join(tempdir,"output.detru"), "r") as f:
    trace["output_tok"] = f.read().strip()
  
  shutil.rmtree(tempdir)
  
  return trace


