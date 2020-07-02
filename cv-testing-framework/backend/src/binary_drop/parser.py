# Parse binary drop for available, already built binaries from DVS. Uses the dvstransfer web interface
# for now, but there may be a more robust way of doing this. However, the HTTP/HTML interface
# seems stable fow now - Calvin - Jan 2020
#
# Interesting to note that some of this data seems to be in the VRL/GG2 database, although
# it does not seem to be exactly what we want. Also, we probably want to store this data locally
# in our database, as we shouldn't rely too much on the stability of VRL/GG2's database interface, which
# is internal and has been exposed to us by request.
#
# More precise results (and richer results) could be obtained by looking directly into the DVS database. However, we can
# get a good approximation by reading the dvstransfer website and parsing binary names.

import requests
from html.parser import HTMLParser
import re

# TODO deprecated
dvs_binaries = "http://dvstransfer.nvidia.com/dvsshare/dvs-binaries/"

cl_extractor = re.compile(r'SW_(\d+(\.\d+)?)')
build_types = ['Release', 'Debug', 'Develop', 'Assert', 'Retail',]
def extract_package_parts(package_name):
    """
    Extract branch and build from a full DVS package name.
    Returns tuple (branch, build, proper name, fullname)
    """
    build = None
    for bt in build_types:
        index = package_name.find(bt)
        if index >= 0:
            build = bt
            break
    if index == -1:
        return ('', '', package_name, package_name)
    branch = package_name[0:index-1]
    shortname = package_name[index + len(build) + 1:]
    return (branch, build, shortname, package_name)

class BinariesHTMLParser(HTMLParser):
    """
    A simple state machine to extract binary URLs and changelists from
    the HTML returned from a binary drop page.
    """

    def __init__(self, urlPrefix, urlDict, extractCls):
        super().__init__()
        self.ignoreFirst = True
        self.urlDict = urlDict
        self.urlPrefix = urlPrefix
        self.inUrlAnchor = False
        self.cl = None
        self.url = None
        self.extractCls = extractCls

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        if self.ignoreFirst:
            self.ignoreFirst = False
            return
        self.url = None
        for (k, v) in attrs:
            if k == "href":
                self.url = self.urlPrefix + v
        self.inUrlAnchor = not not self.url

    def handle_endtag(self, tag):
        if self.inUrlAnchor and tag == "a":
            self.inUrlAnchor = False
            self.urlDict[self.cl] = self.url

    def handle_data(self, data):
        if self.inUrlAnchor:
            if self.extractCls:
                # Gettings CLs for everything in binary drop
                match = cl_extractor.match(data)
                if not match:
                    self.inUrlAnchor = False
                else:
                    self.cl = match[1]
            else:
                # Getting all builds in Binary drop
                self.cl = data[:-1] # strip trailing '/'


def all_builds():
    """
    Get a list of all available builds. May be slow, involves parsing HTML from dvs.
    """
    res = requests.get(dvs_binaries)
    if res.status_code != 200:
        raise Exception('Could not load dvs binaries page')

    driverDict = {}

    # Start parsing HTML
    parser = BinariesHTMLParser(dvs_binaries, driverDict, False)
    parser.feed(res.text)

    return driverDict


def binary_urls(which):
    """
    Get a list of available binary URLs for a given driver/build. Each item is a pair, (changelist, url).
    Urls are fully qualified, and changelists will be strings - and have a decimal after them if you are looking for
    an integer changelist, like "12345678.0"
    """
    url = dvs_binaries + which + "/"
    res = requests.get(url)
    if res.status_code == 404:
        raise Exception('Could not find available drivers for ' + which)
    if res.status_code != 200:
        raise Exception('Unknown error getting driver list for ' + which)

    urlDict = {}

    # Start parsing HTML
    parser = BinariesHTMLParser(url, urlDict, True)
    parser.feed(res.text)

    return urlDict

# Smoke test
if __name__ == "__main__":
    for cl, url in binary_urls('gpu_drv_module_compiler_Develop_Windows_wddm2-x64_Display_Driver').items():
        print(str(cl) + ': ' + str(url))
    print("all_binaries count: " + str(len(all_builds().items())))