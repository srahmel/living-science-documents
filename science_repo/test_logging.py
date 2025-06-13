import os
import django
import logging

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'science_repo.settings')
django.setup()

# Get a logger
logger = logging.getLogger(__name__)

# Write some test log entries
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')

print('Test log entries written. Check the logs directory for the django.log file.')