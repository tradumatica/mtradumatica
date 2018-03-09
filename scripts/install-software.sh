#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

source $ROOT/venv/bin/activate
export LD_LIBRARY_PATH=$ROOT/venv/local/lib:$ROOT/venv/lib
export PKG_CONFIG_PATH=$ROOT/venv/local/pkgconfig


# Compile and install mgiza
cd $ROOT/software/mgiza/mgizapp
cmake -DCMAKE_INSTALL_PREFIX=$ROOT/venv/local
make -j$CORES || exit 1
make install


cd $ROOT/software/mosesdecoder
make -f contrib/Makefiles/install-dependencies.gmake || exit 1
./compile.sh --prefix=$ROOT/venv/local --with-mm --with-probing-p --install-scripts -j$CORES || exit 1

# Fix problem with script

cp $ROOT/venv/local/scripts/merge_alignment.py $ROOT/venv/local/bin/

# Compile and install apertium

cd $ROOT/software/lttoolbox
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES
make install  || exit 1

cd $ROOT/software/apertium
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES 
make install || exit 1

