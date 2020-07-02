"""
This file handles all the operations related to data ingestion.
Exposed At: <host>/api/ingest/..
"""
from urllib.parse import unquote
from flask import Blueprint, jsonify, request
from src.connections import pg_conn # pylint: disable=import-error
from src.my_logger import logger # pylint: disable=import-error
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import time

app = Blueprint('ingest', __name__)

UPLOAD_FOLDER = 'uploads'
DB_SCHEMA = "uploads"
AUDIT_TABLE = "uploads_audit"

@app.route('/', methods=['POST'])
def orchestrate_ingestion():
    """
    Orchestration funtion for ingestion
    """
    status, filename = save_file(request)
    if status:
        conn = pg_conn()
        csv_file = os.path.join(UPLOAD_FOLDER, filename)
        ingest_status, message = copy_csv_to_staging_table(conn=conn, csv_file=csv_file)
        clean_files(filename)
        return jsonify(ingest_status=ingest_status, message=message), 200
    else:
        return jsonify("Ingest Failed"), 200

def copy_csv_to_staging_table(conn, csv_file):
    """
    Importer function to ingest the entire csv.
    :param csv_file: csv file the user is trying upload
    :return: status: true of false
    """
    status = False
    try:
        tail = os.path.split(csv_file)[1]
        csv_name = tail.split('.')[0]
        csv_name = DB_SCHEMA +"."+ csv_name
        data = open(csv_file, 'r')
        column_headers = data.readline().rstrip()
        column_headers = column_headers.split(',')
        
        sql_create = """CREATE TABLE {} ({})"""
        sql_delete = """DROP TABLE IF EXISTS {}"""
        sql_audit = """INSERT INTO {}.{}(tablename, entrydate, table_exist) VALUES('{}', '{}', TRUE)"""
        
        column_headers = [header + " VARCHAR(255)" for header in column_headers]
        column_headers = ", ".join(column_headers)
        
        # open db connection
        logger.info("Opening connection to the Database")
        
        with conn.cursor() as cursor:
            # check if the staging table exists and drop it if it exists
            logger.info("Check whether the old staging table exists")
            cursor.execute(sql_delete.format(csv_name))
            # create a new staging table
            logger.info("Creating the staging table")
            cursor.execute(sql_create.format(csv_name, column_headers))
            # get the file ready to load it in the db
            logger.info("Copying the csv data to the Database")
            cursor.copy_from(data, csv_name, sep=',')
            # commit the changes
            logger.info("Committing the changes")
            update_audit_table(cursor, csv_name.split('.')[1])
        conn.commit()
        status = True
        data.close()
        message = "Success"
    except Exception as e:
        logger.error(e)
        message = str(e)
    logger.info("#################### END OF TRANSACTIONS #######################")
    return status, message


def update_audit_table(cursor, table_name):
    """update audit tables
    """
    try:
        sql = """SELECT * from {}.{} WHERE tablename='{}'"""
        cursor.execute(sql.format(DB_SCHEMA, AUDIT_TABLE, table_name))
        rows = cursor.fetchall()
        if len(rows)>0:
            sql_update = """UPDATE {}.{} SET entrydate='{}', table_exist=TRUE
                            WHERE tablename='{}'"""
            cursor.execute(sql_update.format(DB_SCHEMA, AUDIT_TABLE, get_date(), table_name))
        else:
            sql_audit = """INSERT INTO {}.{}(tablename, entrydate, table_exist) VALUES('{}', '{}', TRUE)"""
            cursor.execute(sql_audit.format(DB_SCHEMA, AUDIT_TABLE, table_name, get_date()))
    except Exception as err:
        logger.error(err)
        raise Exception(str(err))


def get_date():
    """returns the current date"""
    return datetime.today().strftime('%Y-%m-%d')


def save_file(request):
    """Save the incoming file to the 'uploads' directory
    """
    status = False
    filename = None
    try:
        if not os.path.isdir(UPLOAD_FOLDER):
            os.mkdir(UPLOAD_FOLDER)
        #Check if file was received in the request
        if 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            status = True
        else:
            print("No File Received")
    except Exception as err:
        print(str(err))
    return status, filename


def clean_files(filename):
    """removes a given file. 
    The file has to be present in the UPLOAD_FOLDER
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        os.remove(file_path)
        return True
    except Exception as err:
        logger.error(err)
        return False


@app.route('/clean_uploads')
@app.route('/clean_uploads/<string:days>')
def clean_db(days=2):
    """cleanup API for cleaning up all the ingestion jobs. 
    """
    message = None
    tables = []
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = """SELECT * FROM {}.{}
                    WHERE entrydate < DATE(NOW() - INTERVAL '{} DAY')
                    AND table_exist = TRUE
            """
            cursor.execute(sql.format(DB_SCHEMA, AUDIT_TABLE, days))
            rows = cursor.fetchall()
            if len(rows) > 0:
                for row in rows:
                    tables.append(row['tablename'])
                    sql_delete_table = """DROP TABLE {}.{}"""
                    cursor.execute(sql_delete_table.format(DB_SCHEMA, row['tablename']))
                    sql_update_audit = """UPDATE {}.{} SET table_exist=FALSE WHERE tablename='{}'"""
                    sql_update_audit = sql_update_audit.format(DB_SCHEMA, AUDIT_TABLE, row['tablename'])
                    cursor.execute(sql_update_audit)
                conn.commit()
        conn.close()
        message = "Tables that got deleted: "+ ", ".join(tables)
    except Exception as err:
        logger.error(err)
        message = str(err)
    return jsonify(message=message), 200


def load_csv_to_staging_table(filename, staging_table):
    """
    Loads the data into the given the staging table and later truncates it.
    This function should be used only when a trigger or stored procedure acts
    on the staging table.
    """
    try:
        start_time = time.time()
        csv_file = os.path.join(UPLOAD_FOLDER, filename)
        conn = pg_conn()
        with conn.cursor() as cursor:
            copy_sql = """COPY %s FROM STDIN WITH CSV HEADER DELIMITER AS ',' """
            data = open(csv_file, 'r')
            cursor.copy_expert(sql=copy_sql % staging_table, file=data)
            data.close()
            # commit the changes
            truncate_sql = """truncate table {}"""
            cursor.execute(truncate_sql.format(staging_table))
        conn.commit()
        conn.close()
        elapsed_time = time.time() - start_time
        return True, elapsed_time
    except Exception as e:
        return str(e)


def get_row_count(filename):
    """
    Returns the row count of the given file
    """
    try:
        row_count = 0
        csv_file = os.path.join(UPLOAD_FOLDER, filename)
        data = open(csv_file, 'r')
        row_count = row_count = sum(1 for row in data)
        return row_count
    except Exception as e:
        return str(e)