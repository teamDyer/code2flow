"""
This file handles all the operations related to job monitoring for VRL
Exposed At: <host>/api/monitors/..
"""
from urllib.parse import unquote
from flask import Blueprint, jsonify
from src.connections import vrl_conn # pylint: disable=import-error
from src.my_logger import logger # pylint: disable=import-error

app = Blueprint('monitors', __name__)

@app.route('/runningvrljobs', methods=['GET'])
def get_all_running_jobs_on_vrl():
    """get all the running job on VRL for user DVS
    :return: a list of rows
    :rtype: list
    """
    try:
        rows = ()
        conn = vrl_conn()
        with conn.cursor() as cursor:
            sql = '''
                SELECT vrl.job.gpu, vrl.job.status, vrl.job.submitted, vrl.job.jobstarted, vrl.job.notes, vrl.machine.name as MachineName, vrl.tests.testname as TestName  FROM vrl.job 
                JOIN vrl.tests on vrl.job.testId = vrl.tests.id
                JOIN vrl.machine on vrl.job.machineId = vrl.machine.id
                WHERE username='DVS' AND status='RUNNING' LiMIT 1000
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()
        json_res = jsonify(rows)
        return json_res, 200
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400
