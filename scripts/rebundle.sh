#!/bin/bash

NAME=$1
TYPE=$2
LANGS=$3
BUNDLE=$4
OUTPUT=$5

NONTMX=document
TMX=tmx

MYDIR=$(mktemp -d)

tar xf $BUNDLE --directory=$MYDIR
mv $MYDIR/$NONTMX $MYDIR/$NAME.$LANGS.$TYPE
mv $MYDIR/$TMX $MYDIR/$NAME.$LANGS.tmx

rm -Rf $OUTPUT

cd $MYDIR
zip -q -r $OUTPUT .

rm -Rf $MYDIR

