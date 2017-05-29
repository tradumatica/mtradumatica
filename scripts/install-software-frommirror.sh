#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
CORES=$(getconf _NPROCESSORS_ONLN)

source $ROOT/venv/bin/activate
export LD_LIBRARY_PATH=$ROOT/venv/local/lib:$ROOT/venv/lib
export PKG_CONFIG_PATH=$ROOT/venv/local/pkgconfig

if [ ! -d $ROOT/software ]; then
  mkdir $ROOT/software
fi

# Download zlib
if [ ! -d $ROOT/software/zlib ]; then
  cd $ROOT/software
  wget "http://zlib.net/zlib-1.2.8.tar.gz" -O zlib.tar.gz
#  wget "http://downloads.sourceforge.net/project/libpng/zlib/1.2.8/zlib-1.2.8.tar.gz" -O zlib.tar.gz
  mkdir zlib && tar xzf zlib.tar.gz -C zlib --strip-component 1
  rm zlib.tar.gz
fi

# Compile zlib
cd $ROOT/software/zlib
./configure --prefix=$ROOT/venv/local
make -j$CORES || exit 1
make install || exit 1

# Download boost
if [ ! -d $ROOT/software/boost ]; then
  cd $ROOT/software
  wget "http://mirror.liquidtelecom.com/sourceforge/b/bo/boost/boost/1.61.0/boost_1_61_0.tar.bz2" -O boost.tar.bz2 || exit 1
  #wget "http://sourceforge.net/projects/boost/files/latest/download?source=files" -O boost.tar.bz2 || exit 1
  mkdir boost && tar xjf boost.tar.bz2 -C boost --strip-components 1
  rm boost.tar.bz2
fi

# Compile boost
cd $ROOT/software/boost
./bootstrap.sh
./b2 install -sZLIB_SOURCE=$ROOT/software/zlib --prefix=$ROOT/venv/local -j$CORES || exit 1

# Download cmph
if [ ! -d $ROOT/software/cmph ]; then
  cd $ROOT/software
  wget "http://mirror.liquidtelecom.com/sourceforge/c/cm/cmph/cmph/cmph-2.0.tar.gz" -O cmph.tar.gz || exit 1
  #wget "http://sourceforge.net/projects/cmph/files/latest/download?source=files" -O cmph.tar.gz || exit 1
  mkdir cmph && tar xzf cmph.tar.gz -C cmph --strip-components 1
  rm cmph.tar.gz
fi

# Compile cmph
cd $ROOT/software/cmph
./configure --prefix=$ROOT/venv/local
make -j$CORES install || exit 1

# Download mgiza
if [ ! -d $ROOT/software/mgiza ]; then
  cd $ROOT/software
  git clone https://github.com/moses-smt/mgiza.git || exit 1
fi

# Compile and install mgiza
cd $ROOT/software/mgiza/mgizapp
cmake -DCMAKE_INSTALL_PREFIX=$ROOT/venv/local -DBOOST_ROOT=$ROOT/venv/local -DBOOST_LIBRARYDIR=$ROOT/venv/local/lib .
make -j$CORES 
make install || exit 1

# Download xmlrpc-c
if [ ! -d $ROOT/software/xmlrpc-c ]; then
  cd $ROOT/software
  wget "http://mirror.liquidtelecom.com/sourceforge/x/xm/xmlrpc-c/Xmlrpc-c%20Super%20Stable/1.39.08/xmlrpc-c-1.39.08.tgz" -O xmlrpc-c.tar.gz || exit 1
  #wget "http://sourceforge.net/projects/xmlrpc-c/files/latest/download?source=files" -O xmlrpc-c.tar.gz || exit 1
  mkdir xmlrpc-c && tar xzf xmlrpc-c.tar.gz -C xmlrpc-c --strip-components 1
  rm xmlrpc-c.tar.gz
fi

# Compile and install xmlrpc-c
cd $ROOT/software/xmlrpc-c
./configure --prefix=$ROOT/venv/local
make -j$CORES
make install || exit 1

# Download mosesdecoder
if [ ! -d $ROOT/software/mosesdecoder ]; then
  cd $ROOT/software
  git clone https://github.com/moses-smt/mosesdecoder.git || exit 1

fi

# Compile and install mosesdecoder
cd $ROOT/software/mosesdecoder
git checkout tags/mmt-mvp-v0.12.1 || exit 1 # set tag of 2015/08/10
./bjam link=shared --with-cmph=$ROOT/venv/local --with-boost=$ROOT/venv/local --with-xmlrpc-c=$ROOT/venv/local --with-mm --with-probing-p  --prefix=$ROOT/venv/local --install-scripts -j$CORES || exit 1
cp $ROOT/venv/local/scripts/merge_alignment.py  $ROOT/venv/local/bin/

# Download fast_align

if [ ! -d $ROOT/software/fast_align ]; then
  cd $ROOT/software
  git clone https://github.com/clab/fast_align.git
fi

# Compile and instal fast_align
cd $ROOT/software/fast_align
cmake .
make -j$CORES || exit 1
cp fast_align atools force_align.py $ROOT/venv/local/bin #make install does not exist

# Download redis
if [ ! -d $ROOT/software/redis-stable ]; then
  cd $ROOT/software
  wget http://download.redis.io/redis-stable.tar.gz
  tar xzf redis-stable.tar.gz
  rm redis-stable.tar.gz
fi

cd $ROOT/software/redis-stable
make -j$CORES PREFIX=$ROOT/venv/local install || exit 1
#cp src/redis-server src/redis-check-aof src/redis-benchmark \
#   src/redis-check-dump src/redis-cli  \
#   src/redis-sentinel $ROOT/venv/local/bin

# Download apertium


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
