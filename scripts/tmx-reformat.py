import sys

for i in sys.stdin:
    print(i.rstrip()
           .replace("<!--", "")
           .replace("-->", "")
           .replace("<p><tuv", "<tuv")
           .replace("</tuv></p>", "</tuv>")
         )
    