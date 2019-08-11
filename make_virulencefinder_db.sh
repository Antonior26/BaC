#!/bin/sh

# Install kma alingner
cd ./apps/
git clone https://bitbucket.org/genomicepidemiology/kma.git
cd kma && make

# Install VirulenceFinder Database
cd ../../databases/
git clone https://bitbucket.org/genomicepidemiology/virulencefinder_db.git
cd virulencefinder_db
python3 INSTALL.py ../../apps/kma/kma_index