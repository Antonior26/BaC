#!/bin/bash

# wait for PSQL server to start
echo "Waiting 10s for PSQL to start"
sleep 15
# migrate db, so we have the latest db schema
echo "Running Migrations"
python manage.py migrate --noinput
# Create superuser and load reference data
echo "Creating SuperUser"
python manage.py runscript create_superuser
#echo "Starting the initial data"
python manage.py runscript load_initial_data
echo "collecting static files"
python manage.py collectstatic --noinput
# start development server on public ip interface, on port 8000
echo "creating ARO DB"
python manage.py runscript create_arodb
echo "Starting Application"
python manage.py runserver 0.0.0.0:8000