#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

export PATH=$ROOT/venv/local/bin:$PATH
export LD_LIBRARY_PATH=$ROOT/venv/local/lib
TOK=$ROOT/venv/local/scripts/tokenizer/tokenizer.perl
DETOK=$ROOT/venv/local/scripts/tokenizer/detokenizer.perl
TRU=$ROOT/venv/local/scripts/recaser/truecase.perl
DETRU=$ROOT/venv/local/scripts/recaser/detruecase.perl

ENGINE=$1
DIRECTORY=$2
MYTMPDIR=$(mktemp -d)

usage()
{
  program=$(basename $0)
  echo "$program <model> <output_directory> <input >output" 1>&2;
}


if [ ! -d $DIRECTORY ]; then mkdir $DIRECTORY; fi
if [ $# -lt 1 ]; then usage; exit 1; fi
if [ ENGINE == "" ]; then usage; exit 1; fi
if [ ! -d $ROOT/translators/$ENGINE ]; then echo $ROOT/translators/$ENGINE; echo "Model not found" 1>&2; exit 1; fi

L1=$(python -c 'print("'$ENGINE'".split("-")[1])')
L2=$(python -c 'print("'$ENGINE'".split("-")[2])')


OLDDIR=$(pwd)
cd $ROOT/translators/$ENGINE

if [ -f "moses.tuned.ini" ]; then
	INIFILE="moses.tuned.ini"
else
	INIFILE="moses.ini"
fi

tee $MYTMPDIR/input | \
$TOK -q -l $L1 | \
tee $MYTMPDIR/input.tok | \
$TRU --model sl.tcm | \
tee $MYTMPDIR/input.tru | \
moses -config $INIFILE \
      -translation-details $MYTMPDIR/translation-details.txt \
      -alignment-output-file $MYTMPDIR/alignments.txt \
      -sort-word-alignment \
      -output-unknowns $MYTMPDIR/unknown-words.txt \
      -n-best-list $MYTMPDIR/nbest-list.txt 100 \
      -threads $CORES 2>/dev/null | \
tee $MYTMPDIR/output.tru | \
$DETRU | \
tee $MYTMPDIR/output.detru | \
$DETOK -q -l $L2 >$MYTMPDIR/output 

cd $OLDDIR
mv $MYTMPDIR/* $DIRECTORY

rm -Rf $MYTMPDIR
