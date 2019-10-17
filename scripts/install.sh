#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

$ROOT/scripts/install-python.sh  || exit 1
$ROOT/scripts/install-software.sh || exit 1
$ROOT/scripts/write-config.sh || exit 1
$ROOT/scripts/compile-translations.sh || exit 1

echo "SUCCESS!"
 