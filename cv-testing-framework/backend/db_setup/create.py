"""
Initialize fresh Postgres database. This moves our database schema so to say into source control, and
should help enable local testing, etc.
"""

import os
import pathlib
import psycopg2
import argparse

def run_sql_file(connection, cliargs, filename, keep_going=False, params={}):
    """
    Execute a file of sql against the database. Does not return any results, simply
    execute the file for side effects. Don't put embedded semicolons in strings for this -
    this shouldn't happen in the set up scripts but this function is not completely general purpose
    in that regard.

    connection is a psycopg2 connection object.
    filename is a relative file path to this file (create.py).
    keep_going is a flag that indicates if a single statement failing should stop the whole script. If true,
        errors from individual statements will not stop the whole script.
    """
    fullpath = os.path.join(pathlib.Path(__file__).parent.absolute(), filename)
    with open(fullpath, "r") as file:
        data = file.read()
        parts = [x for x in data.split(';') if x.strip() != '']
        with connection.cursor() as cursor:
            if keep_going:
                for part in parts:
                    try:
                        cursor.execute(part, params)
                    except psycopg2.Error as e:
                        if cliargs.verbose:
                            print(f'failed to execute statement {str(part).strip()}: {str(e).strip()}')
                        else:
                            print(f'failed to execute statement: {str(e).strip()}')
                print(f"executed file {filename}")
            else:
                try:
                    for part in parts:
                        cursor.execute(part, params)
                    print(f"executed file {filename}")
                except psycopg2.Error as e:
                    print(f'failed to execute file {fullpath}: {str(e).strip()}')

def setup(args):
    """
    Connect to database and create tables, roles, etc. The goal here is not to make code to generate every test table we are using, but
    to generate enough such that we can do local testing and experimentation. 

    Gets parameters from environment variables.
    COMPILER_HUB_DATABASE_CREDENTIALS: how to connect with psycopg2 to database - default is 'postgresql:///', which is the local cluster and default database.
    COMPILER_HUB_BACKEND_PASSWORD: the password for the 'backend' user. Defaults to 'iitsoi'.
    COMPILER_HUB_BACKEND_READONLY_PASSWORD: the password for the 'backend_readonly' user. Defaults to 'iitsoi'.
    """
    creds = os.environ.get('COMPILER_HUB_DATABASE_CREDENTIALS', 'postgresql:///')
    params = {
        'backend_password': os.environ.get('COMPILER_HUB_BACKEND_PASSWORD', 'iitsoi'),
        'backend_readonly_password': os.environ.get('COMPILER_HUB_BACKEND_READONLY_PASSWORD', 'iitsoi'),
    }
    with psycopg2.connect(creds) as conn:
        conn.autocommit = True
        run_sql_file(conn, args, "initial.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "denormalizers.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "binarydrop.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "ops.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "scrapedapics.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "scrapedbenchmarks.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "gfx_apics.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "gfx_benchmarks.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "simple.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "nvogtest.sql", keep_going=True, params=params)
        run_sql_file(conn, args, "satellite.sql", keep_going=True, params=params)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="Print more debugging information.", action="store_true")
    args = parser.parse_args()
    setup(args)
