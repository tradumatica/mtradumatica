#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

source $ROOT/venv/bin/activate
export LD_LIBRARY_PATH=$ROOT/venv/local/lib:$ROOT/venv/lib
export PKG_CONFIG_PATH=$ROOT/venv/local/pkgconfig

# Compile and install zlib
cd $ROOT/software/zlib
./configure --prefix=$ROOT/venv/local
make -j$CORES || exit 1
make install || exit 1

# Compile and install boost
cd $ROOT/software/boost
./bootstrap.sh
./b2 install -sZLIB_SOURCE=$ROOT/software/zlib --prefix=$ROOT/venv/local -j$CORES || exit 1

# Compile and install cmph
cd $ROOT/software/cmph
./configure --prefix=$ROOT/venv/local
make -j$CORES install || exit 1

# Compile and install mgiza
cd $ROOT/software/mgiza/mgizapp
cmake -DCMAKE_INSTALL_PREFIX=$ROOT/venv/local -DBOOST_ROOT=$ROOT/venv/local -DBOOST_LIBRARYDIR=$ROOT/venv/local/lib .
make -j$CORES 
make install || exit 1

# Compile and install xmlrpc-c
cd $ROOT/software/xmlrpc-c/trunk
./configure --prefix=$ROOT/venv/local
make -j$CORES
make install || exit 1

# Compile and install mosesdecoder
cd $ROOT/software/mosesdecoder
git checkout tags/mmt-mvp-v0.12.1 || exit 1 # set tag of 2015/08/10
./bjam link=shared --with-cmph=$ROOT/venv/local --with-boost=$ROOT/venv/local --with-xmlrpc-c=$ROOT/venv/local --with-mm --with-probing-p  --prefix=$ROOT/venv/local --install-scripts -j$CORES || exit 1
cp $ROOT/venv/local/scripts/merge_alignment.py  $ROOT/venv/local/bin/

# Compile and install fast_align
cd $ROOT/software/fast_align
cmake .
make -j$CORES || exit 1
cp fast_align atools force_align.py $ROOT/venv/local/bin #make install does not exist

# Compile and install apertium

cd $ROOT/software/lttoolbox
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES
make install  || exit 1

cd $ROOT/software/apertium
./autogen.sh --prefix=$ROOT/venv/local
make -j$CORES 
make install || exit 1
