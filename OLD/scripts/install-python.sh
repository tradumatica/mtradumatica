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

pip install Babel==2.1.1
pip install blinker==1.4
pip install coverage==4.0.1
pip install decorator==4.0.4
pip install Flask==0.10.1
pip install Flask-Babel==0.9
pip install Flask-Login==0.3.2
pip install Flask-Mail==0.9.1
pip install Flask-OpenID==1.2.5
pip install Flask-SQLAlchemy==2.1
pip install Flask-WhooshAlchemy==0.56
pip install Flask-WTF==0.12
pip install flipflop==1.0
pip install guess-language==0.2
pip install itsdangerous==0.24
pip install Jinja2==2.8
pip install langid==1.1.5
pip install MarkupSafe==0.23
pip install numpy==1.10.1
pip install pbr==1.8.1
pip install python-magic==0.4.10
pip install python-openid==2.2.5
pip install pytz==2015.7
pip install six==1.10.0
pip install speaklater==1.3
pip install SQLAlchemy==1.0.9
pip install sqlalchemy-migrate==0.10.0
pip install sqlparse==0.1.18
pip install Tempita==0.5.2
pip install Werkzeug==0.10.4
pip install wheel==0.24.0
pip install Whoosh==2.7.0
pip install WTForms==2.0.2
pip install celery
pip install redis
pip install regex
pip install gunicorn
