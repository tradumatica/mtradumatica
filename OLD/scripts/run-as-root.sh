apt-get update
apt-get install -y python-virtualenv python-dev libbz2-dev git \
                   subversion wget cmake \
                   libgoogle-perftools-dev libsparsehash-dev \
                   libtool libpcre3-dev flex xsltproc gawk \
                   zip unzip libxml2-dev libxml2-utils pkg-config autoconf \
                   coreutils zlib1g-dev libbz2-dev automake git-core build-essential \
                   libboost-all-dev software-properties-common python-software-properties
                   
                   
add-apt-repository -y ppa:chris-lea/redis-server
apt-get update
apt-get install -y redis-server
apt-get autoremove -y                

                    