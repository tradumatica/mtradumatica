FROM ubuntu:18.04

RUN mkdir /opt/mtradumatica
COPY . /opt/mtradumatica/
RUN apt-get update -q --fix-missing && \
    apt-get -y upgrade && \
    apt-get -y install python-virtualenv \
                       python-dev \
                       libbz2-dev \
                       git \
                       wget \
                       cmake \
                       libgoogle-perftools-dev \
                       libsparsehash-dev \
                       libtool \
                       libpcre3-dev \
                       flex \
                       xsltproc \
                       gawk \
                       zip \
                       unzip \
                       libxml2-dev \
                       libxml2-utils \
                       pkg-config \
                       autoconf \
                       coreutils \
                       zlib1g-dev \
                       libbz2-dev \
                       automake \
                       git-core \
                       build-essential \
                       libboost-all-dev \
                       software-properties-common \
                       redis \
                       curl \
                       default-jdk && \
    /opt/mtradumatica/scripts/install.sh && \
    rm -Rf /opt/mtradumatica/software && \  
    apt-get autoremove -y && \
    apt-get autoclean

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

EXPOSE 8080 10000

CMD /opt/mtradumatica/scripts/docker-entrypoint.sh
