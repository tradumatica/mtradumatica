import langid
import os

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

