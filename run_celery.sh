#!/bin/sh

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
celery worker -A BaC -l info -E