import errno
import langid
import os
import psutil
import socket

def count_files(path = '.'):
  try:
    res = len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path,name))])
    return res
  except:
    return 0

def count_dirs(path = '.'):
  try:
    res = len([name for name in os.listdir(path) if os.path.isdir(os.path.join(path,name))])
    return res
  except:
    return 0

def get_size(start_path = '.'):
  total_size = 0
  try:
    if os.path.isdir(start_path):
      for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
          fp = os.path.join(dirpath, f)
          total_size += os.path.getsize(fp)
      return total_size
    elif os.path.isfile(start_path):
      return os.path.getsize(start_path)
  except:
    return 0

class condec(object):
  def __init__(self, dec, condition):
    self.decorator = dec
    self.condition = condition

  def __call__(self, func):
    if not self.condition:
      # Return the function unchanged, not decorated.
      return func
    return self.decorator(func)

def write_upload(input_file, filename):
  output   = open(filename, 'w')

  sz = 0
  nc = 0
  nw = 0
  nl = 0
  excerpt = []
  lang = u""
  for i in input_file:
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

  return sz, nc, nw, nl, lang

def file_properties(input_filename):
  input_file = open(input_filename, 'r')
  sz = 0
  nc = 0
  nw = 0
  nl = 0
  excerpt = []
  lang = u""
  for i in input_file:
    sz += len(i)
    s = unicode(i, errors='ignore')
    nl += 1
    nw += len(s.split())
    nc += len(s)

    if nl < 1000:
      excerpt.append(s)
    elif nl == 1000:
      lang = langid.classify(u"".join(excerpt))[0]

  input_file.close()

  if nl < 1000:
    lang = langid.classify(u"".join(excerpt))[0]

  return sz, nc, nw, nl, lang

def recursive_link(source, dest):
  files = next(os.walk(source))[2]
  os.mkdir(dest)
  
  for i in files:
    os.link(os.path.join(source, i), os.path.join(dest,i))


def is_port_used(port_number):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    s.bind(("127.0.0.1", port_number))
  except socket.error, e:
    if e.errno == errno.EADDRINUSE:
      return True
    else:
      return False
  s.close()

def is_proc_alive(nproc):
  for p in psutil.process_iter():
    if p.pid == nproc:
      return True
  else:
    return False
    