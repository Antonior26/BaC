ARG DOCKER_IMAGE_BASE=continuumio/miniconda3

# Virtualenv setup
FROM ${DOCKER_IMAGE_BASE} as venv

# Prpare image to install python packages
RUN set NO_PROXY=continuum.io,anaconda.org
RUN apt-get update && apt-get install build-essential libz-dev ntp -y

# Install python packages
ADD environment.yml .
RUN conda env create python=3.6 --file environment.yml

# Install kma and virulence finder
WORKDIR /opt/virulencefinder/
RUN git clone https://bitbucket.org/genomicepidemiology/kma.git
RUN cd kma && make && cd /opt/virulencefinder/
RUN git clone https://bitbucket.org/genomicepidemiology/virulencefinder.git
RUN cp virulencefinder/virulencefinder.py .

# Install Resfinder
WORKDIR /opt/
RUN git clone https://bitbucket.org/genomicepidemiology/resfinder.git

# Install Virulencefinder ans Resfinder databases
WORKDIR /databases/
RUN git clone https://git@bitbucket.org/genomicepidemiology/resfinder_db.git
RUN git clone https://bitbucket.org/genomicepidemiology/virulencefinder_db.git
WORKDIR /databases/virulencefinder_db
RUN python INSTALL.py /opt/virulencefinder/kma/kma_index

FROM ${DOCKER_IMAGE_BASE} as base

COPY --from=venv /databases/ /databases/
COPY --from=venv /opt/virulencefinder/ /opt/virulencefinder/
COPY --from=venv /opt/resfinder/ /opt/resfinder/
COPY --from=venv /opt/conda/envs /opt/conda/envs
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:/opt/conda/bin:$PATH

# Install perl. TODO: find a better way of installing perl
RUN apt-get update && apt-get install build-essential libz-dev ntp -y
RUN wget http://cdn-fastly.deb.debian.org/debian/pool/main/libd/libdatetime-timezone-perl/libdatetime-timezone-perl_2.23-1+2019c_all.deb
RUN dpkg -i libdatetime-timezone-perl_2.23-1+2019c_all.deb; exit 0
RUN apt-get install -f -y

# Install RASTk
WORKDIR /
RUN wget https://github.com/TheSEED/RASTtk-Distribution/releases/download/v1.3.0/rasttk-v1.3.0.deb
RUN dpkg -i rasttk-v1.3.0.deb; exit 0
RUN apt-get install -f -y
RUN cpanm install JSON::RPC::Client

# Fix rasttk bug
WORKDIR /usr/share/rasttk/deployment/bin
RUN sed -i 's|/home/olson/KB/runtime/|/usr/share/rasttk/runtime/|' *
RUN sed -i 's|//|/|' *


ADD . /app/
RUN adduser --disabled-password --gecos '' admin
ENV PYTHONUNBUFFERED 1
WORKDIR /app/
CMD ['/opt/conda/envs/env/bin/python']