"""
This file manages the data normalization for compiler graphics project for CHUB.
This provides a class to handle the request payload and normalize the data.
"""

import json
import sys
import hashlib
import re
import traceback

def print_psycopg2_exception(err):
    """
    Simple helper for debugging.
    """
    _, _, trace = sys.exc_info()
    if hasattr(err, 'pgcode'):
        print("psycopg2 ERROR:", err, end="")
        print("pgcode:", err.pgcode)
    else:
        print('ERROR: ', err)
    traceback.print_tb(trace)

def insert_data_for_audit(cursor, data):
    """
    This function handles duplicate requests being sent to CHUB.
    Keeps track of how many time the same payload gets requested.
    :param cursor: cursor to the database.
    :param data: request payload
    :return: number of attempts made
    """
    try:
        hex_digest = hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
        insert_sql = """INSERT INTO job_audit(data_hash, data, attempts)
                        VALUES (%s, %s, 1) ON CONFLICT (data_hash, data) DO UPDATE SET attempts = job_audit.attempts + 1
                        RETURNING attempts"""
        params = [hex_digest, json.dumps(data)]
        cursor.execute(insert_sql, params)
        rows = cursor.fetchall()
        return rows[0]['attempts']
    except Exception as err:
        print_psycopg2_exception(err)
        raise err

def make_normalizer(into, columns, conflicts=None):
    """
    Create a normalizer function. This function inserts n columns into a table into and gives the row id,
    returning an existing row id if such a row already exists. The function is also memoized to drastically
    improve performance on repeated inserts, such as would occur in scraping.
    """
    arity = len(columns)
    arglist = '(' + (', ').join(['%s'] * arity) + ')'
    collist = '(' + (', ').join(columns) + ')'
    predicate = (' AND ').join([f"{col} = %s" for col in columns])
    sql = (
        f"WITH new_table as (\n"
        f"    INSERT INTO {into}{collist} VALUES {arglist}\n"
        f"    ON CONFLICT {conflicts or collist} DO NOTHING\n"
        f"    RETURNING id\n"
        f") SELECT COALESCE (\n"
        f"    (SELECT id FROM new_table),\n"
        f"    (SELECT id from {into} WHERE {predicate})\n"
        f") as id"
    )
    def closure(cursor, memo_table, values):
        lenv = len(values)
        if lenv != arity:
            raise Exception(f'Bad arity, expected arguments [{(", ").join(columns)}], got {lenv} values')
        if values in memo_table:
            return memo_table[values]
        try:
            cursor.execute(sql, values * 2)
            row = cursor.fetchall()
            result = row[0]['id']
            memo_table[values] = result
            return result
        except Exception as err:
            print('sql: ' + sql)
            print_psycopg2_exception(err)
            raise err
    return closure
    
gpu_normalizer = make_normalizer('gpus', ['name', 'board_name', 'ram', 'vbios'])
machine_normalizer = make_normalizer('machineconfig', ['name', 'gpu_id', 'cpu', 'cpu_speed', 'os', 'os_build', 'ram'])
p4_normalizer = make_normalizer('p4cl', ['cl', 'virtual'])
branch_normalizer = make_normalizer('branch', ['name', 'build'])
subtest_normalizer = make_normalizer('subtests', ['name'])
testname_normalizer = make_normalizer('tests', ['name'])
user_normalizer = make_normalizer('ldap_user', ['ldap_name'])

def normalize_gpu(cursor, memo, gpu, board_name, gpu_ram, vbios):
    """
    This function handles the normalization of GPU data.
    Adds a new GPU configs if not existing in the db.
    :param cursor: cursor to the database
    :param memo: memoization table
    :param gpu: gpu name
    :param gpu_ram: amount of ram in GPU.
    :return gpu_id: id of the GPU entry
    """
    return gpu_normalizer(cursor, memo, (gpu, board_name, int(gpu_ram), str(vbios)))

def normalize_user(cursor, memo, name):
    """
    Get a user id for a given user name.
    :param cursor: cursor to the database
    :param memo: memoization table
    :param name: ldap user name (email w/o @nvidia.com).
    """
    return user_normalizer(cursor, memo, (name,))

def normalize_test(cursor, memo, name):
    """
    Normalize as test (as in a vrl test).
    :param cursor: cursor to database
    :param memo: memoization table
    """
    return testname_normalizer(cursor, memo, (name,))

def normalize_machine(cursor, memo, machine_name, gpu_id, cpu, cpu_speed, os, os_build, cpu_ram):
    """
    This function handles the normalization of machine data.
    Adds a new machine configuration if not existing in the db.
    :param cursor: cursor to the database
    :param memo: dictionary to cache results of a machine configuration -> machine_config_id to cut down on database lookups.
    :param gpu_id: id of the gpu present on the machine
    :return machine_config_id: id of the machine config record.
    """
    if isinstance(cpu_speed, int) or isinstance(cpu_speed, float):
        cpu_speed = f'{cpu_speed}GHz'
    return machine_normalizer(cursor, memo, (machine_name, gpu_id, cpu, cpu_speed, os, str(os_build), int(cpu_ram)))

p4regex = re.compile(r'^(\d+)(\.(\d+))?$')
def normalize_p4(cursor, memo, cl):
    """
    This method handles the normalization of perforce changelist
    Adds a new commit info if not existing in the db.
    :param cursor: cursor to the database
    :param memo: dictionary to cache results of changelist text -> changelist id.
    :param cl: Changelist text
    :return id: (primary key) id of the commit which can be used a unique identifier.
    """
    match = p4regex.match(cl)
    if not match:
        raise Exception('Invalid p4 changelist: ' + cl)
    cl = int(match[1])
    # We can't put NULL in the database because in SQL, 'NULL = NULL' evaluates to NULL, which makes our
    # normalizer not work. It would also make virtual agnostic queries a bit harder.
    virtual_id = int(match[3] or -1)
    return p4_normalizer(cursor, memo, (cl, virtual_id))

def normalize_branch(cursor, memo, branch, build_type):
    """
    This function handles the normalization of branch data.
    Adds a new branch info if not existing in the db.
    :param cursor: cursor to the database
    :param memo: dictionary to cache results for (branch, build_type) -> branch_id lookup.
    :return branch_id: id of branch record from db
    """
    return branch_normalizer(cursor, memo, (branch, build_type.lower()))

def normalize_subtests(cursor, memo, subtests, set_id=None):
    """
    This function handles the entry of subtest data for each job.
    :param cursor: cursor to the database
    :param memo: dictionary to cache results for subtest name -> subtest id lookup
    :param subtests: array of dict with subtest info
    :param set_id: job id with which the subtests needs to be associated. If not provided, one will be generated.
    :return: set_id
    """
    def get_evo_data_from_subtest(subtest):
        evo_data = {}
        try:
            #evo sampler data starts with evo_sampler
            for key in subtest.keys():
                if 'evo_sampler' in key:
                    evo_data[key] = subtest[key]
        except Exception as err:
            print(err)
        return evo_data
    status = False
    # Create a job id automatically
    job_id = set_id
    if not job_id:
        try:
            cursor.execute('INSERT INTO subtest_set DEFAULT VALUES RETURNING id', [])
            job_id = cursor.fetchall()[0]['id']
        except Exception as err:
            print_psycopg2_exception(err)
            raise err
    func_codes = {"pass": 1, "fail": 2, "error": 3, "skipped": 4}
    try:
        for subtest in subtests:
            subtest_name = subtest['subtest_name'].lower()
            subtest_score = subtest.get('subtest_score', None)
            subtest_func_threshold = subtest.get('subtest_func_threshold', None)
            subtest_func_delta = subtest.get('subtest_func_delta', None)
            subtest_funct_res = subtest.get('subtest_func_res', None)
            if subtest_funct_res:
                subtest_funct_res = subtest_funct_res.lower()
            evo_data = get_evo_data_from_subtest(subtest)
            subtest_id = subtest_normalizer(cursor, memo, (subtest_name,))
            sql = """INSERT INTO subtest_scores(job_id, subtest_id, score, functional_result, functional_threshold, functional_delta, evo_scores)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, subtest_id) DO NOTHING"""
            params = [job_id, subtest_id, subtest_score, subtest_funct_res and func_codes[subtest_funct_res],
                        subtest_func_threshold, subtest_func_delta, json.dumps(evo_data)]
            cursor.execute(sql, params)
    except Exception as err:
        print_psycopg2_exception(err)
        raise err
    return job_id
