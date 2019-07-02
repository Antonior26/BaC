FROM continuumio/miniconda3
RUN set NO_PROXY=continuum.io,anaconda.org
RUN apt-get update && apt-get install build-essential ntp -y
#RUN apt-get install libdatetime-timezone-perl=1:2.23-1+2019a -y
RUN wget http://cdn-fastly.deb.debian.org/debian/pool/main/libd/libdatetime-timezone-perl/libdatetime-timezone-perl_2.23-1+2019a_all.deb
RUN dpkg -i libdatetime-timezone-perl_2.23-1+2019a_all.deb; exit 0
RUN apt-get install -f -y
WORKDIR /
RUN wget https://github.com/TheSEED/RASTtk-Distribution/releases/download/v1.3.0/rasttk-v1.3.0.deb
RUN dpkg -i rasttk-v1.3.0.deb; exit 0
RUN apt-get install -f -y
RUN cpanm install JSON::RPC::Client

# Fix based on: https://github.com/TheSEED/RASTtk-Distribution/issues/2
WORKDIR /usr/share/rasttk/deployment/bin
RUN sed -i 's|/home/olson/KB/runtime/|/usr/share/rasttk/runtime/|' *
RUN sed -i 's|//|/|' *

ENV PYTHONUNBUFFERED 1

# add requirements.txt to the image
ADD . app/
ADD environment.yml /app/environment.yml

# set working directory to /app/
WORKDIR /app/

RUN conda env create python=3.6 --file environment.yml
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:/opt/conda/bin:$PATH

# create unprivileged user
RUN adduser --disabled-password --gecos '' admin

WORKDIR /app/