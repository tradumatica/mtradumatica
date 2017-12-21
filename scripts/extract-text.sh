#!/bin/bash
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

export PATH=$ROOT/venv/local/bin:$PATH
export LD_LIBRARY_PATH=$ROOT/venv/local/lib

APERTIUM_PATH="$ROOT/venv/local/bin"
LTTOOLBOX_PATH="$ROOT/venv/local/bin"
DEFAULT_DIRECTORY="$ROOT/venv/local/share/apertium"

extract_text ()
{
python <(cat <<HERE
import sys

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
    sys.stdout.write("\\n")
  else:
    sys.stdout.write(i)  
HERE
)
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
      extract_text

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
      extract_text 
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

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"
  find "$INPUT_TMPDIR" | grep "content\\.xml\\|styles\\.xml" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-desodt" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | extract_text

  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

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

  if [ "$UWORDS" = "no" ]; then
    OPCIONU="-u";
  else OPCIONU="";
  fi

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"

  find "$INPUT_TMPDIR" | grep "xml" |\
  grep -v -i \\\(settings\\\|theme\\\|styles\\\|font\\\|rels\\\|docProps\\\) |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-deswxml" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | extract_text
    
  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

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
 

  if [ "$UWORDS" = "no" ]; then
    OPCIONU="-u";
  else OPCIONU="";
  fi

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"

  find "$INPUT_TMPDIR" | grep "xml$" |\
  grep "slides\/slide" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-despptx" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | extract_text

  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

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

  unzip -q -o -d "$INPUT_TMPDIR" "$INFILE"
  find "$INPUT_TMPDIR" | grep "sharedStrings.xml" |\
  awk '{printf "<file name=\"" $0 "\"/>"; PART = $0; while(getline < PART) printf(" %s", $0); printf("\n");}' |\
  "$APERTIUM_PATH/apertium-desxlsx" ${FORMAT_OPTIONS} |\
  if [ "$TRANSLATION_MEMORY_FILE" = "" ];
  then cat;
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | extract_text 

  rm -Rf "$INPUT_TMPDIR"

  if [ "$BORRAFICHERO" = "true" ]; then
    rm -Rf "$INFILE";
  fi

  rm -Rf "$TMCOMPFILE"
}

translate_htmlnoent ()
{
  "$APERTIUM_PATH/apertium-deshtml" ${FORMAT_OPTIONS} "$INFILE" | \
    if [ "$TRANSLATION_MEMORY_FILE" = "" ]; then
    cat
  else "$APERTIUM_PATH/lt-tmxproc" "$TMCOMPFILE";
  fi | extract_text

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
  2)
    SALIDA=$2
    REDIR=">"
    INFILE=$1
    if [[ ! -e "$INFILE" ]]; then
      echo "Error: file '$INFILE' not found."
      message
    fi
    ;;
  1)
    INFILE=$1
    if [[ ! -e "$INFILE" ]]; then
      echo "Error: file '$INFILE' not found."
      message
    fi
    ;;
  *)
    message
    ;;
esac


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
     fi | extract_text 

