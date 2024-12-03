# celery.py
import os
from celery import Celery
from celery.schedules import crontab, timedelta

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_project.settings')

app = Celery('stock_project')
app.config_from_object('django.conf:settings', namespace='CELERY')


# Beat schedule configuration
app.conf.beat_schedule = {
    # Task to get stocks data every 30 seconds
    'get_stocks_data_30s': {
        'task': 'stocks.tasks.get_stocks_data',
        'schedule': 30.0,  # Runs every 30 seconds
    },

}


# Automatically discover tasks from installed Django apps
app.autodiscover_tasks()
