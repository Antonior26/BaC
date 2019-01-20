FROM continuumio/miniconda3
RUN set NO_PROXY=continuum.io,anaconda.org
RUN apt-get update && apt-get install build-essential ntp -y
RUN wget https://github.com/TheSEED/RASTtk-Distribution/releases/download/v1.3.0/rasttk-v1.3.0.deb
ENV PYTHONUNBUFFERED 1

# add requirements.txt to the image
ADD environment.yml /app/environment.yml

# set working directory to /app/
WORKDIR /app/

RUN conda env create python=3.6 --file environment.yml
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:/opt/conda/bin:$PATH

# create unprivileged user
RUN adduser --disabled-password --gecos '' admin

RUN dpkg -i rasttk-v1.2.0.deb; exit 0
RUN apt-get install -f -y