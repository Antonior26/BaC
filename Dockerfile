ARG DOCKER_IMAGE_BASE=continuumio/miniconda3

# Virtualenv setup
FROM ${DOCKER_IMAGE_BASE} as venv

# Prpare image to install python packages
RUN set NO_PROXY=continuum.io,anaconda.org
RUN apt-get update && apt-get install build-essential libz-dev ntp -y

# Install python packages
ADD environment.yml .
RUN conda env create python=3.6 --file environment.yml

# Install kma 
WORKDIR /opt/
RUN git clone https://bitbucket.org/genomicepidemiology/kma.git
RUN cd kma && make

# Install VirulenceFinder and database
WORKDIR /opt/
RUN git clone https://bitbucket.org/genomicepidemiology/virulencefinder.git
RUN cp virulencefinder/virulencefinder.py .
WORKDIR /databases/
RUN git clone https://bitbucket.org/genomicepidemiology/virulencefinder_db.git
WORKDIR /databases/virulencefinder_db
RUN python INSTALL.py /opt/kma/kma_index

######

FROM ${DOCKER_IMAGE_BASE} as base

COPY --from=venv /databases/ /databases/
COPY --from=venv /opt/virulencefinder/ /opt/virulencefinder/
COPY --from=venv /opt/conda/envs /opt/conda/envs
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:/opt/conda/bin:$PATH

# Install MentaLIST and database

WORKDIR /opt/
RUN julia -e 'using Pkg; Pkg.add("Distributed")'
RUN julia -e 'using Pkg; Pkg.add("ArgParse")'
RUN julia -e 'using Pkg; Pkg.add("BioSequences")'
RUN julia -e 'using Pkg; Pkg.add("JSON")'
RUN julia -e 'using Pkg; Pkg.add("DataStructures")'
RUN julia -e 'using Pkg; Pkg.add("JLD")'
RUN julia -e 'using Pkg; Pkg.add("GZip")'
RUN julia -e 'using Pkg; Pkg.add("Blosc")'
RUN julia -e 'using Pkg; Pkg.add("FileIO")'
RUN julia -e 'using Pkg; Pkg.add("TextWrap")'
RUN julia -e 'using Pkg; Pkg.add("LightXML")'
RUN git clone https://github.com/WGS-TB/MentaLiST.git

WORKDIR /databases/mentalist_db/
ADD databases/mentalist_db/ /databases/mentalist_db/
COPY download_mentalist_databases.sh .
RUN PATH=$PATH:/opt/MentaLiST/src/; \
	./download_mentalist_databases.sh

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