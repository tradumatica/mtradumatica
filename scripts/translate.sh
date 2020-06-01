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

usage()
{
  program=$(basename $0)
  echo "$program <model> <input >output" 1>&2;
}

if [ $# -lt 1 ]; then usage; exit 1; fi
if [ ENGINE == "" ]; then usage; exit 1; fi
if [ ! -d $ROOT/data/translators/$ENGINE ]; then echo $ROOT/data/translators/$ENGINE; echo "Model not found" 1>&2; exit 1; fi

L1=$(python -c 'print "'$ENGINE'".split("-")[1]')
L2=$(python -c 'print "'$ENGINE'".split("-")[2]')

cd $ROOT/data/translators/$ENGINE

if [ -f "moses.tuned.ini" ]; then
	INIFILE="moses.tuned.ini"
else
	INIFILE="moses.ini"
fi

$TOK -q -l $L1 | \
$TRU --model sl.tcm | \
moses -v 0 -f $INIFILE --threads $CORES | \
$DETRU| \
$DETOK -q -l $L2
