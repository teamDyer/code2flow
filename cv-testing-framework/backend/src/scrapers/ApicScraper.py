from .Scraper import Scraper, register_scraper
from .VrlScraper import VrlScraper
from src.connections import vrl_conn
import requests
import zipfile
import re
import io
from psycopg2.extras import Json

@register_scraper('apic')
class ApicScraper(VrlScraper):
    """
    Scrape APICs from VRL. Apics are a special case of VRL jobs, and expect certain columns and data formats.

    Many tests may want to have more columns, though, such as various subtest results, or a blob of
    JSON that contains a tree of options and results. Some other columns like subtest_results will also
    be used if they exist to store subtests.
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
                subtests = None

                # If we need to use test_data.json instead of scraping ourselves, do that
                if self.readJSON:
                    try:
                        record = self.fetch_cached_results(serial)
                        self.writer.insert_dict(record)
                        goodjobs += 1
                    except Exception as e:
                        self.log(f'Error reading test_data.json (serial={serial}): {str(e).rstrip()}')
                        continue

                # Otherwise, do more involved scraping.
                else:
                    try:
                        swak = self.fetch_swak(serial)
                        real_gpu = self.swak_gpu_parse(swak)
                    except Exception as e:
                        self.log(f"Error reading swak (serial={serial}): {str(e)}")
                    if self.wantsSubtests:
                        try:
                            subtests = self.fetch_subtests(serial)
                            job.update({'subtests': subtests})
                        except Exception as e:
                            self.log(f"Error getting subtests (serial={serial}): {str(e)}")

                    # require subtests, or don't add row.
                    if self.wantsSubtests and not subtests:
                        continue

                    try:
                        # Make a base record that we can extend. It should not contain any extra fields, and
                        # should not be missing any fields when we eventually pass it to self.insert_dict.
                        # If extra fields are present or there are missing fields, an exception will be raised.
                        record = {
                            "changelist": job['swChangelist'],
                            "branch": job['branch'],
                            "machine": job['machine'],
                            "gpu_name": real_gpu if real_gpu else job['gpu'],
                            "cpu_name": job['cpu'],
                            "os": job['os'],
                            "time_start": job['time_start'],
                            "time_stop": job['time_stop'],
                            "status": job['status'],
                            "total_score": job['passing'],
                            "original_id": job['serial'],
                            "notes": job['notes'],
                            "group": job['testname']
                        }

                        # Add subtests to row. Subtests can either be a blob (apics), or individual columns
                        # in compute test flags/switches/parameters. Only adds subtests if the destination table
                        # expects them.
                        if 'subtest_results' in self.writer.columns:
                            record['subtest_results'] = Json(subtests)
                        elif 'subtests' in job:
                            for k, v in job['subtests'].items():
                                subcol = 'param_' + k
                                if subcol in self.writer.columns:
                                    record[subcol] = v
                        self.writer.insert_dict(record)
                        goodjobs += 1
                    except Exception as e:
                        self.log(f'error (serial={serial}): {str(e).rstrip()}')
            
            return {"all": jobcount, "good": goodjobs, "ignored": jobcount - goodjobs}
