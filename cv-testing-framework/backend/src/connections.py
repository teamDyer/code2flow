import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.extensions import register_adapter
import pymysql
import pymysql.cursors
import os

# Allow pushing dicts/lists directly for json/jsonb fields.
# this effects how psycopg2's sql quoting works globally.
register_adapter(dict, Json)
register_adapter(list, Json)

# Database credentials should be supplied by the environment.
DB_CREDS = os.environ['COMPILER_HUB_DATABASE_CREDENTIALS']
DB_READONLY_CREDS = os.environ['COMPILER_HUB_DATABASE_READONLY_CREDENTIALS']

def pg_conn(readOnly=False):
    creds = DB_READONLY_CREDS if readOnly else DB_CREDS
    return psycopg2.connect(creds, cursor_factory=RealDictCursor)

# Currently only to austin
# todo - add other vrl database connections if needed.
def vrl_conn():
    return pymysql.connect(
            host='vrlausmasterscrep01',
            user='compverif',
            password='Compver1f@',
            db='vrl',
            port=3306,
            cursorclass=pymysql.cursors.DictCursor)
