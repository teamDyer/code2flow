#
# This subapp exposes VRL functionality and data via HTTP for the frontend.
# New vrl HTTP handlers should go here. VRL submission code currently lives
# in vrlsubmit.py.
#

from flask import Blueprint, jsonify, session, request, g, make_response
from src.auth import auth_wrap
from src.connections import vrl_conn
from src.util import sql_filter_clause

app = Blueprint('vrl', __name__)

#
# Routes
#

@app.route('gpus')
@app.route('gpus/<string:filterstring>')
def get_vrl_gpus(filterstring=""):
    # Pymysql seems to convert a connection in a with statement to a cursor
    with vrl_conn() as cursor:
        try:
            sql = 'SELECT id, name FROM vrl.gpus WHERE ' + sql_filter_clause('name', filterstring) + ';'
            cursor.execute(sql)
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400

@app.route('cpus')
@app.route('cpus/<string:filterstring>')
def get_vrl_cpus(filterstring=""):
    # Pymysql seems to convert a connection in a with statement to a cursor
    with vrl_conn() as cursor:
        try:
            sql = 'SELECT id, name FROM vrl.cpus WHERE ' + sql_filter_clause('name', filterstring) + ';'
            cursor.execute(sql)
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400

@app.route('oses')
@app.route('oses/<string:filterstring>')
def get_vrl_oses(filterstring=""):
    # Pymysql seems to convert a connection in a with statement to a cursor
    with vrl_conn() as cursor:
        try:
            sql = 'SELECT id, name FROM vrl.oses WHERE ' + sql_filter_clause('name', filterstring) + ';'
            cursor.execute(sql)
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400

@app.route('machines')
@app.route('machines/<string:filterstring>')
def get_vrl_machines(filterstring=""):
    # Pymysql seems to convert a connection in a with statement to a cursor
    with vrl_conn() as cursor:
        try:
            sql = 'SELECT id, name, location, description, cpu, gpu FROM vrl.machine WHERE enabled AND ' + sql_filter_clause('name', filterstring) + ';'
            cursor.execute(sql)
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400

@app.route('machines/by-pool/<string:pool>')
def get_vrl_machines_by_pool(pool):
    with vrl_conn() as cursor:
        try:
            sql = '''
            SELECT vrl.machine.id, vrl.machine.name, vrl.machine.location, vrl.machine.description, vrl.machine.cpu, vrl.machine.gpu
            FROM vrl.machine
            JOIN vrl.machinePools_machine ON vrl.machinePools_machine.machineId = vrl.machine.id
            JOIN vrl.machinePools ON vrl.machinePools.id = vrl.machinePools_machine.machinePoolId WHERE vrl.machinePools.name = %s
            '''
            cursor.execute(sql, [pool])
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400

@app.route('servers')
def get_available_servers():
    """
    Get available servers for use in vrlsubmit.

    Return:
    JSON[] of server dictionaries.
        - "name": name of server
        - "description": description of server
    """
    # TODO - add Pune, etc.
    return jsonify([
        {"name": "ausvrl", "description": "VRL in Austin, TX"}
    ])

@app.route('responses')
def get_available_submit_responses():
    """
    Get available options for submission response.

    Return:
    JSON[] of response types.
        - "name": name of field
        - "description": description of response type
    """
    return jsonify([
        {"name": "email",  "description": "Get an email when the job completes."},
        {"name": "none",  "description": "Do not get notified when the job completes."}
    ])

@app.route('all_tests')
@app.route('all_tests/<string:filterstring>')
def get_all_available_tests(filterstring=""):
    """
    Get all available (enabled) tests in VRL. Optionally limit with a filter string.

    Parameters:
    filterstring? - a substring that is searched for in the test string.

    Returns:
    JSON[] of objects.
         - "id": VRL id of test
         - "testname": Name of test
         - "program": which VRL program to use to run the test
         - "triad": argumnets passed to the program 
         - "contact": who to contact for issues related to the test.
    """
    with vrl_conn() as cursor:
        try:
            sql = '''
            SELECT id, testname, program, triad, contact FROM
            vrl.tests WHERE enabled = True AND
            ''' + sql_filter_clause('testname', filterstring) + ';'
            cursor.execute(sql, [])
            rows = list(cursor)
            return jsonify(rows)
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400
