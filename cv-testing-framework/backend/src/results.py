#
# This file manages results that have already been scraped and exposes
# an HTTP API for getting test data.
#
# Exposed at http://cv-framework.nvidia.com/api/results/...
#

from flask import Blueprint, jsonify, session, request, g, make_response
from src.auth import auth_wrap
from src.connections import pg_conn
from src.ingest import save_file, load_csv_to_staging_table, clean_files, get_row_count
from psycopg2 import sql
from src.scrapers import make_scraper
from src.scrapers.TestWriter import TestWriter
from taskq.app import capp
import csv
import io
import traceback

app = Blueprint('results', __name__)

def do_select(conn, query, params):
    """
    Helper for making generic select queries
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor)
    except Exception as e:
        print("SQL query error: " + str(e))
        return None

def make_csv_response(conn, system, name, rows):
    # Given a test system and test name, we want to make
    # First get all of the columns in the that table and
    # use those as CSV headers
    cols = do_select(conn, """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND
                table_name = %s
        ORDER BY ordinal_position;
        """, [system, name]) 
    headers = [c['column_name'] for c in cols] # make sure headers is a list. Possibly not needed?
    out = io.StringIO()
    writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headers)
    for row in rows:
        rowlist = [row[h] for h in headers]
        writer.writerow(rowlist)
    res = make_response(out.getvalue())
    out.close()
    res.headers["Content-Disposition"] = "attachment; filename=export.csv"
    res.headers["Content-type"] = "text/csv"
    return res

def scrape_results(nsec, where_clause, sql_args):
    """
    Scrape for new results, only selecting scrapers where where_clause matches. nsec is the number
    of seconds to look backwards in time for results.
    """
    with pg_conn() as conn:
        rows = None
        with conn.cursor() as cursor:
            sql = '''
            SELECT test_scrapers.id as scrapeid, test_meta.id, test_meta.system, test_meta.name,
                   test_scrapers.scrape_tag, test_scrapers.scrape_params
            FROM test_meta JOIN test_scrapers
            ON test_meta.id = test_scrapers.test_meta_id
            WHERE test_scrapers.enabled AND
            ''' + where_clause
            cursor.execute(sql, sql_args)
            rows = list(cursor)
        print('Running %d scrapers' % len(rows))
        for row in rows:
            try:
                print('Scraping with scraper ' + str(row['scrapeid']))
                scraper = make_scraper(conn, row['scrape_tag'], row['system'], row['name'], row['scrape_params'])
                scraper.scrape_latest(nsec)
            except Exception as e:
                traceback.print_exc()

def scrape_new(nsec):
    """
    Scrape results for all tests, looking for results newer than nsec.
    """
    return scrape_results(nsec, 'true', [])

def scrape_test(system, name, sec=3600*24*10):
    """
    Scrape a single test, looking for results newer than sec.
    """
    return scrape_results(sec, 'test_meta.system = %s AND test_meta.name = %s', [system, name])

#
# Routes
#

@app.route('testinfo/<string:testSystem>/<string:testName>')
def get_testinfo(testSystem, testName):
    """
    Get metadata for a given test.

    Parameters:
    testSystem: string - The name of the test system ('vrl')
    testName: string - the name of the test ('shadertest')

    Returns:
    JSON[] {
        id: integer - id of the test
        system: string - name of the test system
        name: string - name of the test.
        table_name: The name of the table to put results in for this test. Should probably be the same as name.
           Ex: A test with table name 'shadertest' and system 'vrl' would have a table at vrl.shadertest in Postgres
    }

    On Error:
    404, JSON {
        status: "error"
        error: string
    }
    """
    with pg_conn() as conn:
        rows = do_select(conn, 'SELECT id, system, name FROM test_meta WHERE system = %s AND name = %s', [testSystem, testName])
        if rows is None:
            return jsonify({"status": "error", "error": "Test not found"}), 404
        return jsonify(rows)

@app.route('all-tests/<string:testSystem>')
def query_all_tests(testSystem):
    """
    Get all unique tests types in the system. This can be used to check which tests a user wants to view.
    testSystem is a string like "vrl" or "ccv", or can be the string "all" for all test systems.

    Parameters:
    testSystem: string - the name of test system ('vrl')

    Returns:
    JSON[] {
        id: integer - id of the test
        system: string - name of the test system
        name: string - name of the test.
    }
    """
    filter_str = '' if (testSystem == 'all') else ' WHERE system = %s'
    filter_args = [] if (testSystem == 'all') else [testSystem]
    with pg_conn() as conn:
        rows = do_select(conn, 'SELECT * FROM test_meta ' + filter_str + ' ORDER BY system, name;', filter_args)
        if rows is None:
            return jsonify({"status": "error"}), 404
        return jsonify(rows)

# We probably want a variant of this that limits changelists to a range
@app.route('testname/<string:system>/<string:name>')
@app.route('testname/<string:system>/<string:name>/<string:limit>')
def query_testnames(system, name, limit=None):
    """
    Gets test results for a given test. if no limit is given, returns all results in history. Otherwise, limits
    to an integer number of results.

    If a query parameter ?csv=true is given, will return results as a CSV file instead of JSON. This is used
    to download test results as a CSV for further analysis.

    Parameters:
    system: string - the name of the test System ('vrl')
    name: string - the name of the test ('shadertest')
    limit: integer? - optional limit to number of results to get

    Returns:
    Json[] of objects, each representing a row in the results.
    OR
    a CSV file of the test results (with limit rows if limit is given).

    On Error:
    {"status": "error": "error": string}
    """
    with pg_conn() as conn:
        query = None
        if limit:
            query = sql.SQL('SELECT * FROM {}.{} LIMIT {};').format(sql.Identifier(system), sql.Identifier(name), sql.Literal(int(limit)))
        else:
            query = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(system), sql.Identifier(name))
        rows = do_select(conn, query, [])
        if rows is None:
            return jsonify({"status": "error", "error": "Unknown error returning results"}), 404
        elif "csv" in request.args or not request.accept_mimetypes['application/json']:
            return make_csv_response(conn, system, name, rows)
        else:
            return jsonify(rows)

def single_result_getter(system, name, key, value):
    """
    Helper to get a single result based on some key
    """
    with pg_conn() as conn:
        query = sql.SQL('SELECT * FROM {}.{} WHERE {} = %s LIMIT 1;').format(sql.Identifier(system), sql.Identifier(name), sql.Identifier(key))
        rows = do_select(conn, query, [value])
        if rows is None or not rows:
            return jsonify({"status": "error", "error": "test not found"}), 404
        return jsonify(rows[0])

@app.route('job/<string:system>/<string:name>/<string:colname>/<string:value>')
def query_testname_one(system, name, colname, value):
    """
    Get the test result for a single JOB given its original ID.

    Parameters:
    system: string - the name of the test system ('vrl')
    name: string - the name of the test ('shadertest')
    colname: string - the name of column to use a key to look up the test result.
    value: string - the value of the column.

    On Error:
    {"status": "error", "error": string}
    Returns:
    Json object of job results - keys are test dependent.
    """
    return single_result_getter(system, name, colname, value)

@app.route('one/<string:system>/<string:name>/<string:rowid>')
def query_testname_oneid(system, name, rowid):
    """
    Get the test result for a single JOB given its ID. Same as the job route, where colname='id'.

    Parameters:
    system: string - the name of the test system ('vrl')
    name: string - the name of the test ('shadertest')
    rowid: string - the id of the row, as returned by POST /api/results/push/<system>/<name>

    On Error:
    {"status": "error", "error": string}
    Returns:
    Json object of job results - keys are test dependent.
    """
    return single_result_getter(system, name, 'id', rowid)

# Scrape Routes
scrape_one_task = capp.task(scrape_test)
@app.route('scrape-one/<string:system>/<string:name>', methods=['POST'])
def scrape_one_post(system, name):
    """
    Manual trigger a scrape job. Useful mainly for debugging right now.

    Parameters:
    system: string - The name of the test system ('vrl')
    name: string - The name of the test 'shadertest')
    """
    scrape_one_task.delay(system, name)
    return jsonify({"status": "pending"})

# Push Routes

# Insert a record into the database
@app.route('push/<string:system>/<string:name>', methods=['POST'])
def push_record(system, name):
    """
    Add a test result to the compiler hub.

    Parameters:
    system: string - The name of the test system ('vrl')
    name: string - the name of the test ('shadertest')

    Body:
    JSON object containing column names -> column values for the test table. Can also be an array of such obects.

    Returns:
    {"status": "ok", "id": id(s)}
    On Error:
    {"status": "error", "error": string}
    """
    with pg_conn() as conn:
        return_value = None
        scraper = None
        try:
            writer = TestWriter(system, name, conn)

            # Check if json sent.
            json = request.json
            if json is None:
                return jsonify({"status": "error", "error": "expected JSON"})

            if isinstance(json, dict):
                # single row
                return_value = writer.insert_dict(json, dropExtra=False)[0]
            else:
                # many rows
                return_value = writer.insert_dicts(json, dropExtra=False)

        except Exception as e:
            if scraper:
                scraper.log(str(e))
            return jsonify({"status": "error", "error": str(e)})
        return jsonify({"status": "ok", "id": return_value})
    
    
@app.route('push_csv/<string:system>', methods=['POST'])
def push_csv(system):
    """API to push results into CSV format.
    Currently the API only accepts cvc as the system.
    As more teams onboard the function will accomodate
    fetching systems from DB.
    :param system: the system for which the results are pushed. Example cvc
    :type system: string
    :return: json with success or error messages
    :rtype: dict
    """
    try:
        if system != 'cvc':
            raise Exception("System {} not yet supported by HUB".format(system))
        else:
            status, filename = save_file(request)
            if status:
                csv_push_status, elapsed_time = load_csv_to_staging_table(filename, "compute_stage")
                elapsed_time = str("%.2f Seconds" % elapsed_time)
                row_count = get_row_count(filename)
                cleanup_status = clean_files(filename)
            else:
                raise Exception("Unable to process the CSV")
            return jsonify(status=status,
                           push_status=csv_push_status,
                           rows_processed=row_count,
                           elapsed_time=elapsed_time,
                           cleanup_status=cleanup_status)
    except Exception as e:
            return jsonify({"status": "error", "error": str(e)})
        
