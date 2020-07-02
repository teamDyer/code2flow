# Class that implements basic scraping fuctionality, such as
# connecting to the CVF database and uploading data.

import datetime
import psycopg2
from psycopg2 import sql
from src.connections import pg_conn
from src.scrapers.TestWriter import TestWriter

scrapers = {}

# Registry of scrapers. Let's use look up scrapers by tag.
def register_scraper(tag):
    """
    Register a scraper to a tag so we can look it up from a string and instantiate it
    """
    def inner(clazz):
        scrapers[tag] = clazz
        return clazz
    return inner

def make_scraper(conn, tag, test_system, test_name, params):
    """
    Create a scraper of an unknown class given a tag, testname, and parameter object.
    Since these fields are all stored in the database, we can dynamically scrape jobs.
    """
    clazz = scrapers[tag] if tag in scrapers else Scraper
    return clazz(test_system, test_name, params, conn)

class Scraper:
    """
    A scraper gets test result and job information from an external source and puts into
    the postgres database in a unified format. Since data will eventually come from many different
    sources, there are many different kinds of scrapers.

    This is a base class, and concrete scrapers should extend it. The methods that need to be extended are:

    - scrape_one_impl,
    - scrape_latest_impl,
    - scrape_artifacts_impl
    """

    def __init__(self, test_system, test_name, params, conn):
        self.test_system = test_system
        self.test_name = test_name
        self.connection = conn
        self.params = params
        self.writer = TestWriter(test_system, test_name, conn)
    
    def log(self, msg):
        print('scraping %s (%s): %s' % (self.test_name, self.test_system, msg))

    def scrape_one(self, originalId):
        """
        Scrape a single job given it's id, the format of which depends on the test system.
        For VRL, as serial id, but other systems may have a different id, or just a changelist.
        Not all scrapers need to support this, they may raise an error.
        """
        time_start = datetime.datetime.utcnow()
        self.log('scraping job %s, started at %s' % (originalId, time_start))
        self.scrape_one_impl(originalId)
        time_end = datetime.datetime.utcnow()
        self.log('finished scraping job %s at %s - elapsed: %s' % (originalId, time_end, (time_end - time_start)))

    def scrape_latest(self, nsec):
        """
        Scrape latest jobs. Should get jobs from after the datetime 'when'.
        """
        time_start = datetime.datetime.utcnow()
        self.log('scraping jobs newer than %d sec, started at %s' % (nsec, time_start))
        self.scrape_latest_impl(nsec)
        time_end = datetime.datetime.utcnow()
        self.log('finished scraping jobs newer than %d sec at %s - elapsed: %s' % (nsec, time_end, (time_end - time_start)))

    def scrape_one_impl(self, originalId):
        raise Exception('override this')

    def scrape_latest_impl(self, nsec):
        raise Exception('override this')