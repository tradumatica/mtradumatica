import xml.parsers.expat
import re
import pycld2 as cld2

curlang  = ""
curtuv   = []
intuv    = False
p        = re.compile(r'<.*?>')
p1       = re.compile(r'\n')
p2       = re.compile(r'  *')
tu       = {}
exclude  = []

def explore(filename):
  with open(filename, "rb") as fd:
    langset  = set()
    langlist = []
    
    def se(name, attrs):
      if name == "tuv":
        if "xml:lang" in attrs:
          if attrs["xml:lang"].lower() not in langset:
            langlist.append(attrs["xml:lang"].lower())
            langset.add(attrs["xml:lang"].lower())
        elif "lang" in attrs:
          if attrs["lang"] not in langset:
            langlist.append(attrs["lang"].lower())
            langset.add(attrs["lang"].lower())
    
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = se
    p.ParseFile(fd)

    return langlist

def tmx2txt(fd, output, langlist):
  
  def se(name, attrs):
    global intuv, curtuv, tu, curlang
    if intuv:
      curtuv.append("")
    elif name == "tu":
      tu = {i:'' for i in langlist}
    elif name == "tuv":
      if "xml:lang" in attrs:
        curlang = attrs["xml:lang"].lower()
      elif "lang" in attrs:
        curlang = attrs["lang"].lower()
    elif name == "seg":
      curtuv = []
      intuv = True
    
  def ee(name):
    global intuv, curtuv, p, p1, p2, tu, curlang, exclude
    if name == "tu":
      for i in range(len(langlist)):
        lang = langlist[i]
        if cld2.detect(tu[lang].encode("utf-8"))[2][0][1] in exclude:
          print("DISCARDED",tu[lang])
          return
        
      for i in range(len(langlist)):
        lang = langlist[i]
        out  = output[i]
        out.write(tu[lang])
        out.write("\n")
    elif name == "seg":
      intuv = False
      mystr = p2.sub(' ', p1.sub(' ', p.sub(' ', "".join(curtuv)))).strip()
      tu[curlang] = mystr
      curlang = ""
    elif intuv:
      curtuv.append("")

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
  output    = [open(out_prefix + "." + i, "w") for i in lang_list]

  with open(tmx_file, "rb") as input:
    tmx2txt(input, output, lang_list)

  for i in output:
    i.close()

  return [out_prefix + "." + i for i in lang_list]
