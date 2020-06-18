#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

TABLE=$1
PHRASE=$2
LIMIT=$3

if [[ -f $TABLE ]]; then 
    zgrep "^[^|]\+\b$PHRASE\b[^|]\+" $TABLE | head -n $LIMIT
else >&2 echo "Error: missing file"
fi
