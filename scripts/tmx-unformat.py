import re
import sys
import xml.parsers.expat
from xml.sax.saxutils import escape

def print_attrs(attrs):
    if len(attrs) == 0:
        return ""
    else:
        return " "+" ".join(['{}="{}"'.format(n, escape(attrs[n])) for n in attrs])

def process_tmx(input, output, lang1, lang2):
    inside = False
    skip = False
    storage = []

    def se(name, attrs):     
        nonlocal output, inside, skip, storage
        if skip:
            return
        if inside:
            storage.append("<{}{}>".format(name, print_attrs(attrs)))
        if name == "tuv":
            myattr = {"xml:lang", "lang"}.intersection(attrs)
            langattr = next(iter(myattr)) if len(myattr) > 0 else None
            if langattr != None:
                if attrs[langattr] == lang1 or attrs[langattr].startswith("{}-".format(lang1)):
                    inside = True
                    storage = []
                elif attrs[langattr] == lang2 or attrs[langattr].startswith("{}-".format(lang2)):
                    skip = True
                    return

        output.write("<{}{}>".format(name, print_attrs(attrs)))
        

            
    def ee(name):
        nonlocal output, lang2, inside, skip, storage
        
        if skip:
            if name == "tuv":
                skip = False
            return        
        elif name == "tuv":
            inside = False  
        elif name == "tu":
            if len(storage) > 0:
                output.write('<p><tuv xml:lang="{}">{}</tuv></p>'.format(lang2, "".join(storage)))
            storage = []
        elif inside:
            storage.append("</{}>".format(name))
        output.write("</{}>".format(name))

    def cd(data):
        nonlocal output, inside, skip, storage
        
        if skip:
            return
        if inside:
            storage.append(escape(data))

        if re.match("^\s+$", escape(data)):
            output.write("<!--")
            output.write(escape(data))
            output.write("-->")
        else:
            output.write(escape(data))


    
    def xd(version, encoding, standalone):
        nonlocal output        
        output.write('<?xml version="{}" encoding="{}"?>\n'.format(version, encoding))

    def cm(data):
        pass

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler  = se
    p.EndElementHandler    = ee
    p.CharacterDataHandler = cd
    p.XmlDeclHandler = xd
    p.CommentHandler = cm 
    p.ParseFile(input) 

if __name__ == '__main__':
    lang1 = sys.argv[1]
    lang2 = sys.argv[2]
    input = sys.stdin.buffer
    output = sys.stdout
    
    process_tmx(input, output, lang1, lang2)
    
    input.close()
    output.close()

