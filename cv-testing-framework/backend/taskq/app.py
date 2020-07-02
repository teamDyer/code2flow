
from celery import Celery
import celeryconfig

# Export app in separate file so we can easily add tasks from
# src directory without creating circular dependencies. This is convenient
# if we want to keep logic out of the taskq directory, launch tasks from
# http requests, and avoid circuular dependencies.

capp = Celery()
capp.config_from_object(celeryconfig)
