#
# This subapp exposes DSV functionality and data via HTTP for the frontend.
# New dvs HTTP handlers should go here.
#

import urllib
import requests
from flask import Blueprint, jsonify, session, request, g, make_response
from src.auth import auth_wrap
from src.connections import pg_conn
from src.binary_drop.parser import all_builds, binary_urls, extract_package_parts
from src.util import sql_filter_clause

app = Blueprint('dvs', __name__)

dvs_host = 'http://ausdvs.nvidia.com/Query/'
dvs_api = dvs_host + 'User?'
dvs_package_api = dvs_host + 'PackageURLForCL?'
dvs_build_package = 'http://ausdvs.nvidia.com/Services/MakePackage?'

#
# Routes
#

@app.route('getpackagemetadata/')
def getpackagemetadata():
    """
    This Route will return data required for filtering package name
    while selecting package details on test submission page.
    As of now values are hardcoded.
    """
    metadata = {
        "source": {
            "DVS Transfer": "dvs_transfer"
        },
        "build": {
            "Release": "Release",
            "Debug": "Debug",
            "Mixed": "Mixed"
        },
        "os": {
            "Win1064": "Windows",
            "Win1072": "Windows",
            "rhel": "Linux"
        },
        "branch": {
            "gpu_drv_module_compiler": "gpu_drv_module_compiler"
        },
        "isolation_modes":{
            "Regular": "REGULAR",
            "Binary Regression Search": "BRS",
            "Serial Isolation Search": "SIS"
        },
        "default": {
            "isolation_mode": "REGULAR"
        }
    }
    return jsonify(metadata)

@app.route('binarydrop/all_builds/')
@app.route('binarydrop/all_builds/<string:filterstring>')
def binarydrop_all_builds(filterstring=""):
    """
    Get a list available binary builds, like Release, Debug, Develop, etc.
    Takes a filter string that can be used to narrow this down,
    because as of Jan 2020, there are about 68,000 results here, about
    68,000 of which are useless to us.
    The filter string is just a series of search terms concatenated with +.
    The table dvs.binarydrop in postgres is where all of the (potentially)
    available builds are stored - this is updated by a daily scrape job.
    """
    with pg_conn() as conn:
        with conn.cursor() as cursor:
            try:
                sql = 'SELECT name, id FROM dvs.binarydrop WHERE ' + sql_filter_clause('name', filterstring) + ';'
                cursor.execute(sql)
                rows = list(cursor)
                return jsonify(rows)
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 404

@app.route('binarydrop/changelists/<string:drivername>')
def binarydrop_changelists(drivername):
    with pg_conn() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute('''
                    SELECT changelist, url FROM dvs.binarydrop_changelists
                    JOIN dvs.binarydrop ON dvs.binarydrop.id = dvs.binarydrop_changelists.binarydrop_id
                    WHERE dvs.binarydrop.name = %s
                    ORDER BY 1 DESC
                    ''', [drivername])
                res = list(cursor)
                return jsonify(res)
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 404

def scrape_binary_drop_packages():
    """
    Scrape binary drop packages.
    """
    with pg_conn() as conn:
        print("Getting list of build types in binary drop...")
        builds = all_builds()
        names = builds.keys()
        tuples = map(extract_package_parts, names)
        print("Adding list of build types to database")
        with conn.cursor() as cursor:
            cursor.executemany('''INSERT INTO dvs.binarydrop (branch, build, shortname, name, scrape_periodically)
                                  VALUES (%s, %s, %s, %s, false) ON CONFLICT (name) DO NOTHING;''',
                                  list(tuples))
        print("Getting which builds to scrape for specific changelists...")
        to_scrape = []
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, name FROM dvs.binarydrop WHERE scrape_periodically = true;', [])
            to_scrape = list(cursor)
        for scrape_dict in to_scrape:
            name = scrape_dict["name"]
            binarydrop_id = scrape_dict["id"]
            print("Get available changelists for binary drop buildtype " + name + "...")
            cl2urls = binary_urls(name)
            args = [[cl, binarydrop_id, url] for cl, url in cl2urls.items()]
            with conn.cursor() as cursor:
                try:
                    print("Deleting old changelists for binary drop package type " + name + " from database...")
                    cursor.execute('DELETE FROM dvs.binarydrop_changelists WHERE binarydrop_id = %s', [binarydrop_id])
                    print("Adding available changelists for binary drop package type " + name + " to database...")
                    cursor.executemany('''
                        INSERT INTO dvs.binarydrop_changelists (changelist, binarydrop_id, url)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (changelist, binarydrop_id) DO NOTHING;
                        ''',
                        args)
                    # Probably want to vacuum here, although IT might do it for us.
                    # We need this because we are creating a fair bit of row churn here by deleting and then adding.
                    # Since this is run infrequently, it probably will not be an issue.
                except Exception:
                    print('Failed to add changelists')
                    conn.rollback()


@app.route('get_package_url/<string:package>/<string:changelist>')
@app.route('get_package_url/<string:package>/<string:changelist>/<string:p4server>')
def get_package_url(package, changelist, p4server='SW'):
    """Get the URL for a specified package
    :param package: Any valid DVS package name
    :type package: string
    :param changelist: Any changelist
    :type changelist: string
    :param p4server: Which P4 server the change was against, defaults to 'SW'
    :type p4server: string, optional
    :return: package url for the cl provided
    :rtype: dict
    """
    try:
        #url parameters
        url_params = {'which_request':'package_url_request',
                      'which_package':package,
                      'which_changelist':changelist,
                      'which_p4server':p4server}
        url = dvs_api  + urllib.parse.urlencode(url_params)
        #make request to check if a package exists
        resp = requests.get(url)
        #return 404 if package does not exist
        if 'DOESNT_EXIST' in resp.text:
            return resp.text, 404
        else:
            #check if the package actually exists. DVS holds only 30 days worth of builds.
            data = pkg_if_exists(package, changelist)
            package_url = None
            if data[0] == 'SUCCESS':
                package_url = data[2].rstrip()
            return jsonify(package_url=package_url), resp.status_code
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 404


def pkg_if_exists(package, changelist, debug=0):
    """Return package url at a changelist.
    Do not set debug to 1 unless working on local branch.
    Calling functions can handle the result format set for debug=0 
    :param package: Any valid DVS package name
    :type package: string
    :param changelist: The DVS short changelist with optional virtual revision
    :type changelist: string
    :param debug: A flag (1|0) that enables debug output
    :type debug: string, optional
    :return: reponse of the api split into list
    :rtype: list
    """
    try:
        #url parameters
        url_params = {'pkg':package,
                      'sw_cl':float(changelist),
                      'debug':debug}
        url = dvs_package_api  + urllib.parse.urlencode(url_params)
        #make request to check if a package exists
        resp = requests.get(url)
        data = resp.text.split(',')
        return data
    except Exception as e:
        return str(e)


@app.route('get_build_scripts/<string:component>')
def get_build_scripts(component):
    """get the build script for a specified build component
    :param component: Any valid build component
    :type component: string
    :return: the build script
    :rtype: string
    """
    try:
        url_params = {'which_user':'build_script_generator',
                      'build_component':component}
        url = dvs_api + urllib.parse.urlencode(url_params)
        #make request to fetch build scripts
        resp = requests.get(url)
        return resp.text
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 404


@app.route('build_package/<string:user>/<string:package>/<string:changelist>')
def build_package(user, package, changelist):
    """Build package at the given changelist for the given package.
    :param user: auth userid
    :type user: string
    :param package: Name of the DVS package to be built
    :type package: string
    :param changelist: sw_cl to build
    :type changelist: string
    :return: status
    :rtype: string
    """
    try:
        url_params = {'user':user,
                      'package':package,
                      'sw_changelist':changelist}
        url = dvs_build_package + urllib.parse.urlencode(url_params)
        #make request to build a package
        resp = requests.get(url)
        return resp.text, resp.status_code
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 404


@app.route('get_package_tests/<string:package>/<string:test_system>')
def get_package_tests(package, test_system):
    """Get test name list for given package name and test system
    :param package: Any valid DVS package name
    :type package: string
    :param test_system: Test System (Valid values are "VRL", "cvcServer")
    :type test_system: string
    :return: response of the api split into list
    :rtype: list
    """
    with pg_conn() as conn:
        with conn.cursor() as cursor:
            try:
                
                # Get all the test name and filter them based on mapped package name and system id
                cursor.execute('''
                    Select public.tests.name from public.tests
                    Join dvs.test_package_mapping on dvs.test_package_mapping.test_id = public.tests.id
                    Join dvs.binarydrop on dvs.binarydrop.id = dvs.test_package_mapping.package_id
                    Join public.test_system_mapping on public.test_system_mapping.test_id = public.tests.id
                    Join public.test_systems on public.test_systems.id = public.test_system_mapping.system_id
                    where dvs.binarydrop.name = %s AND public.test_systems.name = %s
                    ''', [package, test_system])
                
                res = list(cursor)
                return jsonify(res)
                
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 404

@app.route('get_machineconfig_info/<string:test_names>')
def get_machineconfig_info(test_names):
    """Get machine config which includes gpu list, machine pool names and machine name list
    :param test_names: string of test names separated by "+"
    :type test_names: string
    :return: response of the api split into list
    :rtype: list
    """
    with pg_conn() as conn:
        with conn.cursor() as cursor:
            try:
                
                test_count = 0
                clause = ""
                for test_name in test_names.split('+'):
                    if test_name:
                        test_count += 1
                        if test_count == 1:
                            clause = test_name
                        else:
                            clause = clause + " AND public.tests.name = " + test_name

                query = """Select DISTINCT public.gpus.name as GPUName, public.machineconfig.name as MachineName, public.machine_pools.name MachinePoolName from public.gpus
                        Join public.machineconfig on public.machineconfig.gpu_id = public.gpus.id
                        Join public.test_machine_mapping on public.test_machine_mapping.machine_id = public.machineconfig.vrl_machine_id
                        Join public.tests on public.tests.id = public.test_machine_mapping.test_id
                        Join public.machine_pools on public.machine_pools.id = public.test_machine_mapping.machine_pool_id
                        Where public.tests.name = """
                query = query + clause
                cursor.execute(query)
                
                res = list(cursor)
                return jsonify(res)
                
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 404