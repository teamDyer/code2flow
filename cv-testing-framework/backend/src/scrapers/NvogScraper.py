from .Scraper import Scraper, register_scraper
from .VrlScraper import VrlScraper
from src.connections import vrl_conn
import requests
import zipfile
import re
import io
from psycopg2.extras import Json

@register_scraper('nvog')
class NvogScraper(VrlScraper):
    """
    Scrape Nvog jobs from VRL.
    """

    def scrape_impl(self, where_clause, args):
        with self.vrlconn.cursor() as cursor:
            cursor.execute(self.make_job_query(where_clause), args)
            # Collect stats on how scraping went - all, good, ignored
            jobcount = 0
            goodjobs = 0

            for job in cursor:
                jobcount += 1

                # Get auxiliary data via common VRL artifacts.
                # These subtasks can failed individually
                serial = job['serial']
                swak = None
                real_gpu = None
                try:
                    swak = self.fetch_swak(serial)
                    real_gpu = self.swak_gpu_parse(swak)
                except Exception as e:
                    self.log("Error reading swak: " + str(e))
                
                # Parse nvogtest oglslave.zip
                subtest_results = {}
                zipblob = self.fetch_zip(serial, "oglslave.zip")
                if not zipblob:
                    self.log('Could not find oglslave.zip (serial ' + str(serial) + ')')
                    continue
                try:
                    with zipblob as zipblob:
                        name_regex = re.compile(r'^Nvogtest(-(\d+))?/nvogtest_stdout.txt$')
                        for filename in zipblob.namelist():
                            filename_match = name_regex.match(filename)
                            if not filename_match:
                                continue
                            name = filename_match[2] or ''
                            with zipblob.open(filename) as f:

                                def nextline():
                                    return str(f.readline(), 'utf-8')

                                # Find 'Validate initial state'
                                start_patt = re.compile(r'^Validate initial state')
                                while not start_patt.match(nextline()):
                                    pass

                                # subtest scores
                                section_patt = re.compile(r'^Do\s+(\w+)\s*:\s*([^!]+)!(.*$)?')
                                line = nextline()
                                while line:
                                    m = section_patt.match(line)
                                    if m:
                                        subtest_results[name + ':' + m[1]] = str(m[2]).lower()
                                    else:
                                        break
                                    line = nextline()
                                
                except Exception as e:
                    self.log("Error parsing logfile: " + str(e))
                    continue

                try:
                    # General VRL based fields.
                    record = {
                        "branch": job['branch'],
                        "changelist": job['swChangelist'],
                        "total_score": job['passing'],
                        'subtest_results': subtest_results,
                        "cpu": job['cpu'],
                        "gpu": real_gpu if real_gpu else job['gpu'],
                        "os": job['os'],
                        "machine": job['machine'],
                        "original_id": job['serial'],
                        "status": job['status'],
                        "time_start": job['time_start'],
                        "time_stop": job['time_stop'],
                        "notes": job['notes'],
                        "group": job['testname']
                    }

                    self.writer.insert_dict(record)
                    goodjobs += 1
                except Exception as e:
                    self.log('error: ' + str(e).rstrip())

            self.writer.connection.commit()
            
            return {"all": jobcount, "good": goodjobs, "ignored": jobcount - goodjobs}
