#!/bin/bash

# Section 0: Set environment / check requirements

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

command -v virtualenv >/dev/null 2>&1 || { echo >&2 "Required program virtualenv is not installed. Installing package 'python-virtualenv' is required. Aborting."; exit 1; }


# Section 1: Install Python

# Create virtual environment

cd $ROOT

virtualenv venv

cd -

source $ROOT/venv/bin/activate

# pip-install packages

pip install -r $ROOT/requirements.txt
