import xml.parsers.expat
import re
import pycld2 as cld2

curlang  = ""
curtuv   = []
intuv    = False
p        = re.compile(ur'<.*?>')
p1       = re.compile(ur'\n')
p2       = re.compile(ur'  *')
tu       = {}
exclude  = []

def explore(filename):
  with open(filename, "r") as fd:
    langset  = set()
    langlist = []
    
    def se(name, attrs):
      if name == u"tuv":
        if u"xml:lang" in attrs:
          if attrs[u"xml:lang"].lower() not in langset:
            langlist.append(attrs[u"xml:lang"].lower())
            langset.add(attrs[u"xml:lang"].lower())
        elif u"lang" in attrs:
          if attrs[u"lang"] not in langset:
            langlist.append(attrs[u"lang"].lower())
            langset.add(attrs[u"lang"].lower())
    
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = se
    p.ParseFile(fd)

    return langlist

def tmx2txt(fd, output, langlist):
  
  def se(name, attrs):
    global intuv, curtuv, tu, curlang
    if intuv:
      curtuv.append(u"")
    elif name == u"tu":
      tu = {i:u'' for i in langlist}
    elif name == u"tuv":
      if u"xml:lang" in attrs:
        curlang = attrs[u"xml:lang"].lower()
      elif u"lang" in attrs:
        curlang = attrs[u"lang"].lower()
    elif name == u"seg":
      curtuv = []
      intuv = True
    
  def ee(name):
    global intuv, curtuv, p, p1, p2, tu, curlang, exclude
    if name == u"tu":
      for i in range(len(langlist)):
        lang = langlist[i]
        if cld2.detect(tu[lang].encode("utf-8"))[2][0][1] in exclude:
          print "DISCARDED",tu[lang]
          return
        
      for i in range(len(langlist)):
        lang = langlist[i]
        out  = output[i]
        out.write(tu[lang].encode("utf-8"))
        out.write("\n")
    elif name == u"seg":
      intuv = False
      mystr = p2.sub(u' ', p1.sub(u' ', p.sub(u' ', u"".join(curtuv)))).strip()
      tu[curlang] = mystr
      curlang = u""
    elif intuv:
      curtuv.append(u"")

  def cd(data):
    if intuv:
      curtuv.append(data)

  p = xml.parsers.expat.ParserCreate()
  p.StartElementHandler  = se
  p.EndElementHandler    = ee
  p.CharacterDataHandler = cd
  p.ParseFile(fd) 


def tmx2txt_filelist(tmx_file, out_prefix):
  lang_list = explore(tmx_file)
  output    = [open(out_prefix + "." + i.encode("utf-8"), "w") for i in lang_list]

  with open(tmx_file, "rb") as input:
    tmx2txt(input, output, lang_list)

  for i in output:
    i.close()

  return [out_prefix + "." + i.encode("utf-8") for i in lang_list]
