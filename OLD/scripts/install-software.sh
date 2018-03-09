#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

source $ROOT/venv/bin/activate
export LD_LIBRARY_PATH=$ROOT/venv/local/lib:$ROOT/venv/lib
export PKG_CONFIG_PATH=$ROOT/venv/local/pkgconfig

if [ ! -d $ROOT/software ]; then
  mkdir $ROOT/software
fi

# Download Moses
if [ ! -d $ROOT/software/mosesdecoder ]; then
  cd $ROOT/software
  git clone https://github.com/moses-smt/mosesdecoder.git 
fi

cd $ROOT/software/mosesdecoder
make -f contrib/Makefiles/install-dependencies.gmake || exit 1
./compile.sh --prefix=$ROOT/venv/local --with-mm --with-probing-p --install-scripts -j$CORES || exit 1
cp $ROOT/venv/local/scripts/merge_alignment.py $ROOT/venv/local/bin/

# Download mgiza
if [ ! -d $ROOT/software/mgiza ]; then
  cd $ROOT/software
  git clone https://github.com/moses-smt/mgiza.git || exit 1
fi

# Compile and install mgiza
cd $ROOT/software/mgiza/mgizapp
cmake -DCMAKE_INSTALL_PREFIX=$ROOT/venv/local
make -j$CORES || exit 1
make install

# Compile and install apertium

if [ ! -d $ROOT/software/lttoolbox ]; then
  cd $ROOT/software
  svn co https://svn.code.sf.net/p/apertium/svn/trunk/lttoolbox
fi

cd $ROOT/software/lttoolbox
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES
make install  || exit 1

if [ ! -d $ROOT/software/apertium ]; then
  cd $ROOT/software
  svn co https://svn.code.sf.net/p/apertium/svn/trunk/apertium
fi

cd $ROOT/software/apertium
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES 
make install || exit 1

