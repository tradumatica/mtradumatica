#!/bin/bash

# Section 0: Set environment / check requirements

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

python3 -c "import venv"
if [ $? = 1 ]
then
    echo >&2 "Required program virtualenv is not installed. Installing package 'python-virtualenv' is required. Aborting."; 
    exit 1;
fi

# Section 1: Install Python

# Create virtual environment

cd $ROOT

python3 -m venv venv

cd -

source $ROOT/venv/bin/activate

# pip-install packages
pip3 install wheel
pip3 install -r $ROOT/requirements.txt
