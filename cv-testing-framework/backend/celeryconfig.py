import os

imports = ('taskq.tasks',)
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
enable_utc = True
broker_transport_options = {
    'visibility_timeout': 60 * 5,  # 5 minutes
    'fanout_prefix': True,
    'fanout_patterns': True,
}

if os.environ.get('COMPILER_HUB_NO_SCRAPE'):
    beat_schedule = {
        'health': {
            'task': 'taskq.tasks.health_ping',
            'args': [],
            'schedule': 60 * 10 # every 10 minutes
        },
    }
else:
    beat_schedule = {
        'health': {
            'task': 'taskq.tasks.health_ping',
            'args': [],
            'schedule': 60 * 10 # every 10 minutes
        },
        'scrape-new': {
            'task': 'taskq.tasks.scrape_new',
            'args': [3600 * 48], # look 48 hours back
            'schedule': 3600 * 6 # every 6 hours
        },
        'scrape-binarydrop': {
            'task': 'taskq.tasks.binary_drop_scrape',
            'args': [],
            'schedule': 3600 * 24  # every 24 hours
        },
        'scrape-machine-monitoring': {
            'task': 'taskq.tasks.scrape_machine_monitoring',
            'args': [],
            'schedule': 3600 * 24 # every 24 hours
        }
    }
