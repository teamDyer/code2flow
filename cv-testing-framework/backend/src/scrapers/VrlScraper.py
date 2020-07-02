from .Scraper import Scraper, register_scraper
from src.connections import vrl_conn
from html.parser import HTMLParser
import json
import requests
import zipfile
import re
import io

class ManifestHTMLParser(HTMLParser):
    """
    State Machine to parse HTML for the VRL job page to get a list of available files.
    """

    def __init__(self):
        super().__init__()
        self.in_table = False # only get hrefs if we are in a table row
        self.current_url = None # href of current anchor tag - links to log file
        self.skip = True # skip the first such row (it is a link to the parent directory, ..)
        self.listing = []
        self.listing_dict = {}

    def handle_data(self, data):
        if not self.current_url:
            return
        self.listing_dict[str(data)] = self.current_url

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_table = True
            return
        if not self.in_table:
            return
        if tag != "a":
            return
        for (k, v) in attrs:
            if k == "href":
                if self.skip:
                    self.skip = False
                else:
                    self.current_url = v
                    self.listing.append(v)

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_table = False
        elif tag == "a":
            self.current_url = None

class VrlScraper(Scraper):
    """
    Scrape from VRL. Provides a connection to VRL, as well as useful methods for scraping data
    from individual VRL jobs that are not in the VRL database, but may be in external file-servers,
    the dvs file share, etc.

    Sub-classes should implement scrape_impl.

    For params, this defines how we select VRL jobs to scrape. Only one of the below options is needed.
    - "gg2groupid" - the GG2 groupType ID from VRL to scrape jobs from. Preferred.
    - "gg2pattern" - a pattern to match against VRL test names. Will only match tests that were started by a golden gate two jobs.
    """

    def __init__(self, test_system, test_name, params, conn):
        super().__init__(test_system, test_name, params, conn)
        self.gg2_groupTypeId = params['gg2groupid'] if 'gg2groupid' in params else None
        self.gg2_testpatt = params['gg2pattern'] if 'gg2pattern' in params else (params['gg2group'] if 'gg2group' in params else self.test_name)
        self.wantsSubtests = params['wantsSubtests'] if 'wantsSubtests' in params else True
        self.readJSON = bool(params.get('readJSON'))
        self._listings = {} # file listings for each serial.
        self._listing_dicts = {} # file listings for each serial.
        self.vrlconn = vrl_conn()

    def dvs_url(self, vrl_serial):
        serial_str = str(vrl_serial)
        return "http://ausvrl.nvidia.com/list_result_files.php?job=" + serial_str

    def fetch_file_url(self, vrl_serial, filename):
        """
        Get URL for filename and a vrl serial number
        """
        if str(vrl_serial) not in self._listing_dicts:
            # Need to parse the listings - cache them if not already cached
            parser = self._fetch_listing(vrl_serial)
            self._listings[str(vrl_serial)] = parser.listing
            self._listing_dicts[str(vrl_serial)] = parser.listing_dict
            ldict = parser.listing_dict
        else:
            ldict = self._listing_dicts[str(vrl_serial)]
        return ldict[filename]

    def fetch_file(self, vrl_serial, filename):
        """
        Fetch a text file from VRL. Return None if no file found, otherwise a string of the file's contents. This means
        large files will create large strings.
        """
        url = self.fetch_file_url(vrl_serial, filename)
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.text

    def fetch_summary(self, vrl_serial):
        """
        Get summarylog for a vrl serial job. May not exist (will return None).
        """
        return self.fetch_file(vrl_serial, 'summarylog.txt')

    def fetch_listing_dict(self, vrl_serial):
        """
        Get a dictionary of available files mapping file name to URL.
        """
        return self._fetch_listing(vrl_serial).listing_dict

    def fetch_listing(self, vrl_serial):
        """
        Get list of files available in VRL for a job. Will return an empty list if we can find anything.
        """
        return self._fetch_listing(vrl_serial).listing

    def _fetch_listing(self, vrl_serial):
        """
        Get list of files available in VRL for a job. Will return an empty list if we can find anything.
        """
        url = self.dvs_url(vrl_serial)
        response = requests.get(url)
        if response.status_code != 200:
            return []
        parser = ManifestHTMLParser()
        parser.feed(response.text)
        return parser

    def fetch_zip(self, vrl_serial, name):
        """
        Fetch a .zip file artifact from a VRL job and return a ZipFile. name should include the .zip extension. Will return None
        if no file is found.
        """
        url = self.fetch_file_url(vrl_serial, name)
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return zipfile.ZipFile(io.BytesIO(response.content))

    def fetch_txt_or_zip(self, vrl_serial, filename):
        """
        VRL stores many files in .txt form for a period of time, and then archives them
        to save space later. This first tries to get the .txt file, and then the .zip file.
        filename should not include an extension.
        """
        name_txt = filename + ".txt"
        name_zip = filename + ".zip"
        txt_response = requests.get(self.fetch_file_url(vrl_serial, name_txt))
        txt_body = None
        if txt_response.status_code != 200:
            # [filename].txt does not exist, try [filename].zip
            response = requests.get(self.fetch_file_url(vrl_serial, name_zip))
            if response.status_code != 200:
                # no zip file found either, so give up
                return None
            with zipfile.ZipFile(io.BytesIO(response.content)) as zipblob:
                with zipblob.open(name_txt) as zfile:
                    txt_body = zfile.read()
        else:
            # [filename].txt exists
            txt_body = txt_response.text
        # Decode as utf-8
        if not isinstance(txt_body, str):
            txt_body = str(txt_body, 'utf-8')
        return txt_body

    def fetch_swak(self, vrl_serial):
        """
        Get swak.txt as a string for a given VRL job serial. May not exist.
        """
        return self.fetch_txt_or_zip(vrl_serial, 'swak')

    def fetch_cached_results(self, vrl_serial):
        """
        We can look for a file test_data.json in a job to push more detailed results.
        """
        contents = self.fetch_file(vrl_serial, 'test_data.json')
        return json.loads(contents)

    def swak_parse(self, swak_string, cmd):
        """
        Parse the swak log file for a given command and return the output from that command.
        """
        section_position = swak_string.find("cmd> " + cmd)
        if not section_position:
            return None
        start_position = swak_string.find("\n", section_position) + 1
        end_position = swak_string.find("--------------------------------", start_position)
        return swak_string[start_position:end_position]

    def swak_gpu_parse(self, swak_gpu_output):
        """
        Use swak text to extract a more accurate GPU profile than VRL (which may be out of date).
        """
        # Use only alpha numerics to cut off suffix, like "-A" of GV100-A
        pattern = re.compile(r"Short Name: (\w*)", re.MULTILINE)
        match = pattern.search(swak_gpu_output)
        real_gpu = match[1].strip().lower() if match else None
        return real_gpu

    def fetch_subtests(self, vrl_serial):
        """
        Subtests must be in the format set up by our team.
        """
        url = self.fetch_file_url(vrl_serial, "subtests.txt")
        self.log("Looking for subtests at " + url)
        subtests_response = requests.get(url)
        if subtests_response.status_code == 404:
            self.log('Subtests not found for vrl serial ' + str(vrl_serial))
            return {}
        # subtests.txt is a text file where each line looks like subtest_name=score
        pattern_text = r'^\s*([^=]*)\s*=\s*(\S*)\s*$'
        r = re.compile(pattern_text, re.MULTILINE)
        pairs = r.findall(subtests_response.text)
        # convert scores from strings to numbers
        pairs_number_scores = map(lambda kv: (kv[0], float(kv[1])), pairs)
        # Normalize function status codes -> text
        def get_func_codes(kv):
            key = kv[0]
            value = kv[1]
            if key.endswith('_func'):
                lookup = {
                    0: "Failed",
                    1: "Waived",
                    2: "Passed",
                    3: "Skipped",
                    4: "Blocked",
                    5: "Not Run"
                }
                text = lookup.get(value, value)
                return (key, text)
            else:
                return kv
        pairs_func_codes = map(get_func_codes, pairs_number_scores)
        return dict(pairs_func_codes)

    def make_job_query(self, where_clause):
        return """
        select vrl.job.*,
                CONVERT_TZ(vrl.job.jobstarted, @@global.time_zone, '+00:00') as time_start,
                CONVERT_TZ(vrl.job.finished, @@global.time_zone, '+00:00') as time_stop,
                gg2.tests.result,
                vrl.machine.name as machine,
                gg2.packages.groupId,
                gg2.tests.gpu,
                gg2.submissions.machinePoolName as machinepool,
                gg2.submissions.testname as testname,
                gg2.groupTypes.name as groupName,
                gg2.dvsPackageTypes.branch as branch,
                gg2.changelists.swChangelist from vrl.job
            join vrl.machine on vrl.job.machineId = vrl.machine.id
            join gg2.tests on gg2.tests.serial = vrl.job.serial
            left join gg2.submissions on gg2.submissions.id = gg2.tests.submissionId
            left join gg2.packages on gg2.packages.id = gg2.submissions.packageId
            left join gg2.groups on gg2.groups.id = gg2.packages.groupId
            left join gg2.groupTypes on gg2.groups.groupTypeId = gg2.groupTypes.id
            left join gg2.packageTypes on gg2.packageTypes.id = gg2.packages.packageTypeId
            left join gg2.dvsPackageTypes on gg2.dvsPackageTypes.packageTypeId = gg2.packageTypes.id
            left join gg2.changelists on gg2.groups.changelistId = gg2.changelists.id
        """ + where_clause

    def scrape_one_impl(self, originalId):
        # pylint: disable=no-member
        return self.scrape_impl('WHERE vrl.job.serial = %s', [originalId])

    def scrape_latest_impl(self, nsec):
        # pylint: disable=no-member
        if self.gg2_groupTypeId:
            # For more precise scraping, use a group id over a testname.
            return self.scrape_impl(
                '''
                WHERE gg2.groupTypes.id = %s
                AND vrl.job.finished >= CURDATE() - INTERVAL %s SECOND;
                ''', [self.gg2_groupTypeId, nsec])
        else:
            return self.scrape_impl(
                '''
                WHERE gg2.submissions.testname like %s
                AND vrl.job.finished >= CURDATE() - INTERVAL %s SECOND;
                ''', [self.gg2_testpatt, nsec])