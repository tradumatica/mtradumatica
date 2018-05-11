FROM ubuntu:18.04

RUN mkdir /opt/mtradumatica
ADD ./* /opt/mtradumatica/

RUN apt-get update -q --fix-missing && \
    apt-get -y upgrade && \
    /opt/mtradumatica/scripts/install.sh && \
    rm -Rf /opt/mtradumatica/software && \
    apt-get autoclean

EXPOSE 80 10000

CMD /opt/mtradumatica/scripts/docker-entrypoint.sh
