#!/bin/bash
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

export PATH=$ROOT/venv/local/bin:$PATH
export LD_LIBRARY_PATH=$ROOT/venv/local/lib
TOK=$ROOT/venv/local/scripts/tokenizer/tokenizer.perl
DETOK=$ROOT/venv/local/scripts/tokenizer/detokenizer.perl
TRU=$ROOT/venv/local/scripts/recaser/truecase.perl
DETRU=$ROOT/venv/local/scripts/recaser/detruecase.perl

APERTIUM_PATH="$ROOT/venv/local/bin"
LTTOOLBOX_PATH="$ROOT/venv/local/bin"
DEFAULT_DIRECTORY="$ROOT/venv/local/share/apertium"
ABSOLUTE_PATH_TRANSLATOR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

unbraid ()
{
python <(cat <<HERE
import sys

with open(sys.argv[1], "w") as other:
  nline = 0
  for i in sys.stdin:
    nline += 1
    if i.startswith('<b c="') and i.endswith('"/>\\n'):
      other.write("{0}\\t{1}".format(nline, i))
    else:
      sys.stdout.write(i)
HERE
) $1
}

braid ()
{
python <(cat <<HERE
import sys

dicblocks = {}

with open(sys.argv[1], "r") as other:
  for i in other:
    parts    = i.split("\\t")
    dicblocks[parts[0]] = parts[1]

nline = 0
for i in sys.stdin:
  nline += 1
  
  if str(nline) in dicblocks:
    sys.stdout.write(dicblocks[str(nline)])
    nline += 1
    
  sys.stdout.write(i)
else:
  if str(nline+1) in dicblocks:
    sys.stdout.write(dicblocks[str(nline+1)])  
    
HERE
) $1
}

p2f ()
{
python <(cat <<HERE
import sys
import base64

def next_df_token(input):
  preline = False
  for i in input:
    a = i.rstrip("\\n")
    if preline and a.startswith('<b c="') and a.endswith('"/>'):
      preline = False
      yield base64.b64decode(a[6:-3])
    elif preline:
      yield "\\n"
      yield a
      preline = True
    else:
      yield a
      preline = True

for i in next_df_token(sys.stdin):
  sys.stdout.write(i)
HERE
)  
}

f2p ()
{
python <(cat <<HERE
import sys
import base64

def next_df_token(input):
  buf = []
  skipNext = False
  inside = False
  for i in input:
    for j in i:
      if j == "[" and not skipNext:
        inside = True
        buf = []
        buf.append(j)
      elif j == "]" and not skipNext:
        inside = False
        buf.append(j)
        yield "".join(buf)
      elif inside:
        buf.append(j)
      else:
        yield j

      if j != "\\\\" or skipNext:
        skipNext = False
      else:
        skipNext = True

for i in next_df_token(sys.stdin):
  if len(i) > 1:
    sys.stdout.write('\\n<b c="')
    sys.stdout.write(base64.b64encode(i))
    sys.stdout.write('"/>\\n')
  else:
    sys.stdout.write(i)  
HERE
)
}

translate ()
{

MYTMPDIR=$(mktemp -d)

if [ -f "$ROOT/translators/$ENGINE/moses.tuned.ini" ]; then
	INIFILE="$ROOT/translators/$ENGINE/moses.tuned.ini"
else
	INIFILE="$ROOT/translators/$ENGINE/moses.ini"
fi

cd $ROOT/translators/$ENGINE

f2p | \
unbraid $MYTMPDIR/unb | \
$TOK -q -l $L1 2>/dev/null | \
$TRU --model sl.tcm | \
moses -monotone-at-punctuation -v 0 -f $INIFILE --threads $CORES | \
$DETRU| \
$DETOK -q -l $L2 2>/dev/null > $MYTMPDIR/detok

braid $MYTMPDIR/unb <$MYTMPDIR/detok | \
p2f

rm -Rf $MYTMPDIR
}

message ()
{
  echo "USAGE: $(basename $0) [-d datadir] [-f format] [-u] <direction> [in [out]]"
  echo " -d datadir       directory of linguistic data"
  echo " -f format        one of: txt (default), html, rtf, odt, docx, wxml, xlsx, pptx,"
  echo "                  xpresstag, html-noent, latex, latex-raw"
  echo " -a               display ambiguity"
  echo " -u               don't display marks '*' for unknown words"
  echo " -n               don't insert period before possible sentence-ends"
  echo " -m memory.tmx    use a translation memory to recycle translations"
  echo " -o direction     translation direction using the translation memory,"
  echo "                  by default 'direction' is used instead"
  echo " -l               lists the available translation directions and exits"
  echo " direction        typically, LANG1-LANG2, but see modes.xml in language data"
  echo " in               input file (stdin by default)"
  echo " out              output file (stdout by default)"
  exit 1
}

list_directions ()
{
  echo "";
}

locale_utf8 ()
{
  export LC_CTYPE=$(locale -a|grep -i "utf[.]*8"|head -1);
  if [ LC_CTYPE = "" ]; then
    echo "Error: Install an UTF-8 locale in your system";
    exit 1;
  fi
}

locale_latin1 ()
{
  export LC_CTYPE=$(locale -a|grep -i -e "8859-1" -e "@euro"|head -1);
  if [ LC_CTYPE = "" ]; then
    echo "Error: Install a Latin-1 locale in your system";
    exit 1;
  fi
}

test_zip ()
{
  if [ "$(which zip)" = "" ]; then
    echo "Error: Install 'zip' command in your system";
    exit 1;
  fi

  if [ "$(which unzip)" = "" ]; then
    echo "Error: Install 'unzip' command in your system";
    exit 1;
  fi
}

test_gawk ()
{
  GAWK=$(which gawk)
  if [ "$GAWK" = "" ]; then
    echo "Error: Install 'gawk' in your system"
    exit 1
  fi
}


translate_latex()
{
  test_gawk

  if [ "$INFILE" = ""  -o "$INFILE" = /dev/stdin ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi

  if [ "$(file -b --mime-encoding "$INFILE")" == "utf-8" ]; then
    locale_latin1
  else locale_utf8
  fi

  "$APERTIUM_PATH/apertium-prelatex" "$INFILE" | \
    "$APERTIUM_PATH/apertium-utils-fixlatex" | \
    "$APERTIUM_PATH/apertium-deslatex" ${FORMAT_OPTIONS} | \
    if [ "$TRANSLATION_MEMORY_FILE" = "" ];
    then cat;
    else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
    fi | \
      translate | \
      "$APERTIUM_PATH/apertium-relatex"| \
      awk '{gsub("</CONTENTS-noeos>", "</CONTENTS>"); print;}' | \
      if [ "$REDIR" == "" ]; then "$APERTIUM_PATH/apertium-postlatex-raw"; else "$APERTIUM_PATH/apertium-postlatex-raw" > "$SALIDA"; fi

    if [ "$BORRAFICHERO" = "true" ]; then
      rm -Rf "$INFILE"
    fi
}


translate_latex_raw()
{
  test_gawk

  if [ "$INFILE" = "" -o "$INFILE" = /dev/stdin ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi

  if [ "$(file -b --mime-encoding "$INFILE")" = "utf-8" ]; then
    locale_latin1
  else locale_utf8
  fi

  "$APERTIUM_PATH/apertium-prelatex" "$INFILE" | \
    "$APERTIUM_PATH/apertium-utils-fixlatex" | \
    "$APERTIUM_PATH/apertium-deslatex" ${FORMAT_OPTIONS} | \
    if [ "$TRANSLATION_MEMORY_FILE" = "" ];
    then cat;
    else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
    fi | \
      translate | \
      "$APERTIUM_PATH/apertium-relatex"| \
      awk '{gsub("</CONTENTS-noeos>", "</CONTENTS>"); print;}' | \
      if [ "$REDIR" == "" ]; then "$APERTIUM_PATH/apertium-postlatex-raw"; else "$APERTIUM_PATH/apertium-postlatex-raw" > "$SALIDA"; fi
}


translate_odt ()
{
  INPUT_TMPDIR=$(mktemp -d "$TMPDIR/apertium.XXXXXXXX")

  locale_utf8
  test_zip

  if [ "$INFILE" = "" ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi
  OTRASALIDA=$(mktemp "$TMPDIR/apertium.XXXXXXXX")

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"
  find "$INPUT_TMPDIR" | grep "content\\.xml\\|styles\\.xml" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-desodt" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | \
    translate | \
    "$APERTIUM_PATH/apertium-reodt"|\
  awk '{punto = index($0, "/>") + 3; cabeza = substr($0, 1, punto-1); cola = substr($0, punto); n1 = substr(cabeza, index(cabeza, "\"")+1); name = substr(n1, 1, index(n1, "\"")-1); gsub("[?]> ", "?>\n", cola); print cola > name;}'
  VUELVE=$(pwd)
  cd "$INPUT_TMPDIR"
  rm -Rf ObjectReplacements
  zip -q -r - . >"$OTRASALIDA"
  cd "$VUELVE"
  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

  if [ "$REDIR" == "" ]; then cat "$OTRASALIDA"; else cat "$OTRASALIDA" > "$SALIDA"; fi
  rm -Rf "$OTRASALIDA"
  rm -Rf "$TMCOMPFILE"
}

translate_docx ()
{
  INPUT_TMPDIR=$(mktemp -d "$TMPDIR/apertium.XXXXXXXX")

  locale_utf8
  test_zip

  if [ "$INFILE" = "" ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi
  OTRASALIDA=$(mktemp "$TMPDIR/apertium.XXXXXXXX")

  if [ "$UWORDS" = "no" ]; then
    OPCIONU="-u";
  else OPCIONU="";
  fi

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"

  for i in $(find "$INPUT_TMPDIR"|grep "xlsx$");
  do LOCALTEMP=$(mktemp "$TMPDIR/apertium.XXXXXXXX");
    $ABSOLUTE_PATH_TRANSLATOR -f xlsx -d "$DATADIR" "$OPCIONU" "$PAIR" <"$i" >"$LOCALTEMP";
    cp "$LOCALTEMP" "$i";
    rm "$LOCALTEMP";
  done;

  find "$INPUT_TMPDIR" | grep "xml" |\
  grep -v -i \\\(settings\\\|theme\\\|styles\\\|font\\\|rels\\\|docProps\\\) |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-deswxml" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | \
    translate | \
    "$APERTIUM_PATH/apertium-rewxml"|\
  awk '{punto = index($0, "/>") + 3; cabeza = substr($0, 1, punto-1); cola = substr($0, punto); n1 = substr(cabeza, index(cabeza, "\"")+1); name = substr(n1, 1, index(n1, "\"")-1); gsub("[?]> ", "?>\n", cola); print cola > name;}'
  VUELVE=$(pwd)
  cd "$INPUT_TMPDIR"
  zip -q -r - . >"$OTRASALIDA"
  cd "$VUELVE"
  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

  if [ "$REDIR" == "" ]; then cat "$OTRASALIDA"; else cat "$OTRASALIDA" > "$SALIDA"; fi
  rm -Rf "$OTRASALIDA"
  rm -Rf "$TMCOMPFILE"
}

translate_pptx ()
{
  INPUT_TMPDIR=$(mktemp -d "$TMPDIR/apertium.XXXXXXXX")

  locale_utf8
  test_zip

  if [ "$INFILE" = "" ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi
  OTRASALIDA=$(mktemp "$TMPDIR/apertium.XXXXXXXX")

  if [ "$UWORDS" = "no" ]; then
    OPCIONU="-u";
  else OPCIONU="";
  fi

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"

  for i in $(find "$INPUT_TMPDIR"|grep "xlsx$"); do
    LOCALTEMP=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    $ABSOLUTE_PATH_TRANSLATOR -f xlsx -d "$DATADIR" "$OPCIONU" "$PAIR" <"$i" >"$LOCALTEMP";
    cp "$LOCALTEMP" "$i"
    rm "$LOCALTEMP"
  done;

  find "$INPUT_TMPDIR" | grep "xml$" |\
  grep "slides\/slide" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-despptx" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | \
  translate | \
    "$APERTIUM_PATH/apertium-repptx" |\
  awk '{punto = index($0, "/>") + 3; cabeza = substr($0, 1, punto-1); cola = substr($0, punto); n1 = substr(cabeza, index(cabeza, "\"")+1); name = substr(n1, 1, index(n1, "\"")-1); gsub("[?]> ", "?>\n", cola); print cola > name;}'
  VUELVE=$(pwd)
  cd "$INPUT_TMPDIR"
  zip -q -r - . >"$OTRASALIDA"
  cd "$VUELVE"
  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

  if [ "$REDIR" == "" ]; then cat "$OTRASALIDA"; else cat "$OTRASALIDA" > "$SALIDA"; fi
  rm -Rf "$OTRASALIDA"
  rm -Rf "$TMCOMPFILE"
}


translate_xlsx ()
{
  INPUT_TMPDIR=$(mktemp -d "$TMPDIR/apertium.XXXXXXXX")

  locale_utf8
  test_zip

  if [ "$INFILE" = "" ]; then
    INFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
    cat > "$INFILE"
    BORRAFICHERO="true"
  fi
  OTRASALIDA=$(mktemp "$TMPDIR/apertium.XXXXXXXX")

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"
  find "$INPUT_TMPDIR" | grep "sharedStrings.xml" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-desxlsx" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | \
  translate | \
    "$APERTIUM_PATH/apertium-rexlsx" |\
  awk '{punto = index($0, "/>") + 3; cabeza = substr($0, 1, punto-1); cola = substr($0, punto); n1 = substr(cabeza, index(cabeza, "\"")+1); name = substr(n1, 1, index(n1, "\"")-1); gsub("[?]> ", "?>\n", cola); print cola > name;}'
  VUELVE=$(pwd)
  cd "$INPUT_TMPDIR"
  zip -q -r - . >"$OTRASALIDA"
  cd "$VUELVE"
  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

  if [ "$REDIR" == "" ]; then cat "$OTRASALIDA"; else cat "$OTRASALIDA" > "$SALIDA"; fi
  rm -Rf "$OTRASALIDA"
  rm -Rf "$TMCOMPFILE"
}

translate_htmlnoent ()
{
  "$APERTIUM_PATH/apertium-deshtml" ${FORMAT_OPTIONS} "$INFILE" | \
    if [ "$TRANSLATION_MEMORY_FILE" = "" ]; then
    cat
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | \
  translate | \
  if [ "$FORMAT" = "none" ]; then
    if [ "$REDIR" == "" ]; then cat; else cat > "$SALIDA"; fi
  else if [ "$REDIR" == "" ]; then "$APERTIUM_PATH/apertium-rehtml-noent"; else "$APERTIUM_PATH/apertium-rehtml-noent" > "$SALIDA"; fi
  fi

  rm -Rf "$TMCOMPFILE"
}





##########################################################
# Option and argument parsing, setting globals variables #
##########################################################
PATH="${APERTIUM_PATH}:${PATH}"
[[ -z $TMPDIR ]] && TMPDIR=/tmp
TMCOMPFILE=$(mktemp "$TMPDIR/apertium.XXXXXXXX")
trap 'rm -Rf "$TMCOMPFILE"' EXIT

# Default values, may be overridden below:
PAIR=""
INFILE="/dev/stdin"
FORMAT="txt"
DATADIR=$DEFAULT_DIRECTORY
TRANSLATION_MEMORY_DIRECTION=$PAIR
LIST_MODES_AND_EXIT=false
FORMAT_OPTIONS=""

# Skip (but store) non-option arguments that come before options:
declare -a ARGS_PREOPT
declare -i OPTIND=1
while [[ $OPTIND -le $# ]]; do
  arg=${@:$OPTIND:1}
  case $arg in
    -*) break ;;
    *) ARGS_PREOPT+=($arg); (( OPTIND++ )) ;;
  esac
done


while getopts ":uahlf:d:m:o:n" opt; do
  case "$opt" in
    f) FORMAT=$OPTARG ;;
    d) DATADIR=$OPTARG ;;
    m) TRANSLATION_MEMORY_FILE=$OPTARG ;;
    o) TRANSLATION_MEMORY_DIRECTION=$OPTARG ;;
    u) UWORDS="no" ;;
    n) FORMAT_OPTIONS="-n" ;;
    a) OPTION_TAGGER="-m" ;;
    l) LIST_MODES_AND_EXIT=true ;;
    h) message ;;
    \?) echo "ERROR: Unknown option $OPTARG"; message ;;
    :) echo "ERROR: $OPTARG requires an argument"; message ;;
  esac
done
shift $(($OPTIND-1))

if $LIST_MODES_AND_EXIT; then list_directions; exit 0; fi

# Restore non-option arguments that came before options back into arg list:
set -- "${ARGS_PREOPT[@]}" "$@"

case "$#" in
  3)
    SALIDA=$3
    REDIR=">"
    INFILE=$2
    PAIR=$1
    if [[ ! -e "$INFILE" ]]; then
      echo "Error: file '$INFILE' not found."
      message
    fi
    ;;
  2)
    INFILE=$2
    PAIR=$1
    if [[ ! -e "$INFILE" ]]; then
      echo "Error: file '$INFILE' not found."
      message
    fi
    ;;
  1)
    PAIR=$1
    ;;
  *)
    message
    ;;
esac

ENGINE=$PAIR

L1=$(python -c 'print "'$ENGINE'".split("-")[1]')
L2=$(python -c 'print "'$ENGINE'".split("-")[2]')


if [[ -n $TRANSLATION_MEMORY_FILE ]]; then
  "$APERTIUM_PATH/lt-tmxcomp" "$TRANSLATION_MEMORY_DIRECTION" "$TRANSLATION_MEMORY_FILE" "$TMCOMPFILE" >/dev/null
  if [ "$?" != "0" ]; then
    echo "Error: Cannot compile TM '$TRANSLATION_MEMORY_FILE'"
    echo"   hint: use -o parameter"
    message
  fi
fi

if [[ ! -d "$DATADIR/modes" ]]; then
  echo "Error: Directory '$DATADIR/modes' does not exist."
  message
fi

#Parametro opcional, de no estar, lee de la entrada estandar (stdin)

case "$FORMAT" in
  none)
    if [ "$UWORDS" = "no" ]; then
      OPTION="-n";
    else OPTION="-g";
    fi
    ;;
  txt|rtf|html|xpresstag|mediawiki)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    ;;
  rtf)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    MILOCALE=$(locale -a|grep -i -v "utf\|^C$\|^POSIX$"|head -1);
    if [ "$MILOCALE" = "" ]; then
      echo "Error: Install a ISO-8859-1 compatible locale in your system";
      exit 1;
    fi
    export LC_CTYPE=$MILOCALE
    ;;

  odt)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_odt
    exit 0
    ;;
  latex)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_latex
    exit 0
    ;;
  latex-raw)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_latex_raw
    exit 0
    ;;
  
  
  docx)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_docx
    exit 0
    ;;
  xlsx)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_xlsx
    exit 0
    ;;
  pptx)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_pptx
    exit 0
    ;;
  html-noent)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    translate_htmlnoent
    exit 0
    ;;
  
  wxml)
    if [ "$UWORDS" = "no" ]; then OPTION="-n";
    else OPTION="-g";
    fi;
    locale_utf8
    ;;
  
  txtu)
    FORMAT="txt";
    OPTION="-n"
    ;;
  htmlu)
    FORMAT="html";
    OPTION="-n";
    ;;
  xpresstagu)
    FORMAT="xpresstag";
    OPTION="-n";
    ;;
  rtfu)
    FORMAT="rtf";
    OPTION="-n";
    MILOCALE=$(locale -a|grep -i -v "utf\|^C$\|^POSIX$"|head -1);
    if [ "$MILOCALE" = "" ]; then
      echo "Error: Install a ISO-8859-1 compatible locale in your system";
      exit 1;
    fi
    export LC_CTYPE=$MILOCALE
    ;;

  odtu)
    OPTION="-n"
    translate_odt
    exit 0
    ;;

  docxu)
    OPTION="-n"
    translate_docx
    exit 0
    ;;

  xlsxu)
    OPTION="-n"
    translate_xlsx
    exit 0
    ;;

  pptxu)
    OPTION="-n"
    translate_pptx
    exit 0
    ;;

  wxmlu)
    OPTION="-n";
    locale_utf8
    ;;



  *) # Por defecto asumimos txt
    FORMAT="txt"
    OPTION="-g"
    ;;
esac

if [ -z "$REF" ]
then
    REF=$FORMAT
fi

set -e -o pipefail

if [ "$FORMAT" = "none" ]; then
    cat "$INFILE"
else
  "$APERTIUM_PATH/apertium-des$FORMAT" ${FORMAT_OPTIONS} "$INFILE"
fi | if [ "$TRANSLATION_MEMORY_FILE" = "" ];
     then
         cat
     else
       "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE"
     fi | translate | if [ "$FORMAT" = "none" ]; then
                   if [ "$REDIR" = "" ]; then
                       cat
                   else
                     cat > "$SALIDA"
                   fi
               else
                 if [ "$REDIR" = "" ]; then
                     "$APERTIUM_PATH/apertium-re$FORMAT"
                 else
                   "$APERTIUM_PATH/apertium-re$FORMAT" > "$SALIDA"
                 fi
               fi

