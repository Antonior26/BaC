import logging
import os

from django.contrib.auth.models import User

logging.basicConfig(level=logging.INFO)


def run():
    logging.warning('This script will create a superuser based on the values of environment variables:  SUPERUSER,'
                    'SUPERUSER_PASSWORD and SUPERUSER_EMAIL, make sure you have set this variables and you are not'
                    'using default values in production system')
    logging.info('Checking for superuser in DB...')
    if not User.objects.filter(username=os.getenv('SUPERUSER', 'bac')):
        User.objects.create_superuser(
            email=os.getenv('SUPERUSER_EMAIL'),
            username=os.getenv('SUPERUSER', 'bac'),
            password=os.getenv('SUPERUSER_PASSWORD', 'bac')
        )
        logging.info('Superuser {} has been created.'.format(os.getenv('SUPERUSER', 'bac')))
    else:
        logging.info('Superuser {} already exists, nothing to do.'.format(os.getenv('SUPERUSER', 'bac')))