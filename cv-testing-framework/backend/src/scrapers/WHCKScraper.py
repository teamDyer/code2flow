import xml.etree.ElementTree as ET
from .Scraper import register_scraper
from .VrlScraper import VrlScraper

@register_scraper('whck')
class WHCKScraper(VrlScraper):
    """
    Scrape WHCK (Windows Hardware Certification Kit) jobs from VRL. (gg2 groupType = 6503)
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

                # Read all XML files and parse out information.
                xml_files = [x for x in self.fetch_listing(serial) if x.endswith('.xml')]
                subtest_ids = {}
                subtests = {}
                for file_name in xml_files:
                    try:
                        content = self.fetch_file(serial, file_name)
                        root = ET.fromstring(content)
                        for test_group in root.iter('StartTestGroup'):
                            ctx = test_group.find('ctx').get('id')
                            subtest_ids[ctx] = test_group.get('UserText')
                        for rollup in root.iter('GroupRollup'):
                            ctx = rollup.find('ctx').get('id')
                            subtests[subtest_ids[ctx]] = {
                                'total': int(rollup.get('Total')),
                                'passed': int(rollup.get('Passed')),
                                'failed': int(rollup.get('Failed')),
                                'blocked': int(rollup.get('Blocked')),
                                'warned': int(rollup.get('Warned')),
                                'skipped': int(rollup.get('Skipped'))
                            }
                    except Exception as e:
                        self.log('Failed to parse result file ' + file_name + ' : ' + str(e))
                        continue

                try:
                    # General VRL based fields.
                    record = {
                        "branch": job['branch'],
                        "changelist": job['swChangelist'],
                        "total_score": job['passing'],
                        'subtest_results': subtests,
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
