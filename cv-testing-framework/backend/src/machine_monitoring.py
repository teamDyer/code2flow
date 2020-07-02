"""
This file is to help with machine monitoring

Exposed at http://cv-framework.nvidia.com/api/machine_monitor/...

"""
from flask import Blueprint, jsonify
from src.connections import pg_conn, vrl_conn
from src.my_logger import logger
import datetime

app = Blueprint('machine_monitoring', __name__)


def fetch_distinct_machine():
    """Fetch a list of distinct machines from the machine monitoring table
    """
    machines = []
    conn = pg_conn()
    with conn.cursor() as cursor:
        machine_sql = """SELECT distinct(name)
                         FROM machine_monitoring"""
        cursor.execute(machine_sql)
        rows = cursor.fetchall()
        for row in rows:
            machines.append(row['name'])
    conn.close()
    return machines


def get_machine_monitoring_data_from_vrl(cursor, days):
    """get all the machine monitoring data from the vrl database.
    :param cursor: cursor to the database.
    :type cursor: cursor
    :param days: The max number of days of data that need to scrapped.
    :type days: integer
    """
    sql = """
        SELECT jobdate, name, gpu, count(serial) as jobcount,sum(mindiff) as totaltime
        FROM (
            SELECT distinct j.serial, m.name, m.gpu, 
            TIMESTAMPDIFF(MINUTE, j.jobstarted , j.finished) AS mindiff, DATE(submitted) as jobdate
            FROM machine m, machinePools mp, machinePools_machine mpm, job j
            WHERE j.machineId = m.id
            AND m.id = mpm.machineId
            AND mp.id = mpm.machinePoolId
            AND mp.name like %s AND DATE(submitted) = DATE(NOW() - INTERVAL %s DAY)
            AND j.username = 'ausdata') as temp 
        GROUP BY name"""
    cursor.execute(sql, ("Compiler-Graphics%", days))
    rows = cursor.fetchall()
    machines = fetch_distinct_machine()
    for row in rows:
        name = row['name']
        if name in machines:
            machines.remove(name)
    insert_into_chub(rows, machines)

def insert_into_chub(vrl_data, missing_machines):
    """insert the machine monitoring data into CHUB database
    :param vrl_data: dict of machine monitoring data.
    :type vrl_data: dict
    :param missing_machines: list of machines that missed job execution
    :type missing_machines: list
    """
    jobdate = vrl_data[0]['jobdate']
    conn = pg_conn()
    with conn.cursor() as cursor:
        insert_sql = """INSERT INTO machine_monitoring(jobdate, name, gpu, jobcount, totaltime)
                        VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
        for row in vrl_data:
            params = [str(row['jobdate']), row['name'], row['gpu'], str(row['jobcount']), str(row['totaltime'])]
            print(params)
            cursor.execute(insert_sql, params)
            cursor.execute("COMMIT")

        for machine in missing_machines:
            sql = """
                    SELECT jobdate, gpu 
                    from machine_monitoring 
                    where name=%s 
                    ORDER BY 1
                    limit 1"""
            cursor.execute(sql, [machine])
            gpu = cursor.fetchall()
            gpu = gpu[0]['gpu']
            params = [str(jobdate), machine, gpu, "0", "0"]
            print(params)
            cursor.execute(insert_sql, params)
            conn.commit()
    conn.close()

@app.route('/get_latest')
def orchestrate():
    """Orchestration for scraping machine data from VRL
    and inserting into compiler HUB
    """
    try:
        days = 2
        conn = vrl_conn()
        with conn.cursor() as cursor:
            for i in range(days, 1, -1):
                get_machine_monitoring_data_from_vrl(cursor, i)
        conn.close()
        return jsonify("Scrapping completed"), 200
    except Exception as err:
        return(str(err)), 400


@app.route('/')
@app.route('/<int:days>')
@app.route('/<int:days>/<string:filter_by>')
def get_machine_details_from_postgres(days=7, filter_by="totaltime"):
    """
    api funtion used by the UI to get the machine details.
    Currently the limit is set for the last 10 days.
    In futute this 10 days limit will be controlled via the UI.
    :return: list of dict of machine details
    :rtype: list
    """
    filters = ['totaltime', 'jobcount']
    try:
        days = days + 2
        if filter_by not in filters:
            filter_by = filters[0]
        sql = """
                SELECT * 
                FROM machine_monitoring 
                WHERE jobdate >DATE(NOW() - INTERVAL '%s DAY')
                ORDER BY jobdate"""
        result = {}
        dates = []
        conn = pg_conn()
        with conn.cursor() as cursor:
            cursor.execute(sql, [days])
            rows = cursor.fetchall()
            for row in rows:
                job_date = str(row['jobdate'])
                machine = row['name']
                gpu = row['gpu']
                total_time = int(row[filter_by])
                if job_date not in dates:
                    dates.append(job_date)
                if gpu in result:
                    result_gpu = result[gpu]
                    if machine in result_gpu:
                        result[gpu][machine].append(total_time)
                    else:
                        result[gpu][machine] = [total_time]
                else:
                    temp = {}
                    temp[machine] = [total_time]
                    result[gpu] = temp
        return jsonify(results=result, dates=dates, filter_by=filter_by)
    except Exception as e:
        print(e)
        logger.error(e)
        return jsonify("ERROR"), 400


@app.route('/machinepools')
def machine_pooling():
    """
    API function to get a list of all machines along with its
    GPU information which belong to any Compiler-Graphics machine pool
    :return: list of dict of machine and machine pool details
    :rtype: list
    """
    try:
        conn = vrl_conn()
        with conn.cursor() as cursor:
            sql = """
                SELECT m.name as machine_name, m.gpu as gpu,mp.name as pool_name
                FROM machine m, machinePools mp, machinePools_machine mpm
                WHERE m.id = mpm.machineId
                AND mp.id = mpm.machinePoolId
                AND mp.name like 'Compiler-Graphics%'
                ORDER BY 3"""
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as err:
        print(err)
        logger.error(err)
        return jsonify("ERROR", str(err)), 400