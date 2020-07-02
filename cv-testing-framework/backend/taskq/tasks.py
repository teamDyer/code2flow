from taskq.app import capp
from src.dvs import scrape_binary_drop_packages
from src.machine_monitoring import orchestrate
from src.results import scrape_new, scrape_test

# Do not put too much logic in this file! Instead, import the main functionality
# from a module in the source directory.

@capp.task
def scrape_test_task(system, name, sec=3600*24*10):
    return scrape_test(system, name, sec)

@capp.task
def scrape_new_task(nsec):
    return scrape_new(nsec)

@capp.task
def health_ping():
    print('Healthy...')

@capp.task
def binary_drop_scrape():
    return scrape_binary_drop_packages()

@capp.task
def scrape_machine_monitoring():
    """task to scrape machine monitoring data.
    """
    return orchestrate()