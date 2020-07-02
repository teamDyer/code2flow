#!/usr/bin/env python

from aiohttp import web, ClientSession, ClientTimeout
from base64 import urlsafe_b64encode
import argparse
import asyncio
import datetime
import json
import jsonschema
import os
import shelve
import shutil
import signal
import socket
import sys
import traceback
import uuid
from aiohttp_middlewares import (
    cors_middleware,
    error_middleware
)

#
# Globals
#

VERSION = "0.0.0"
JOBS = {}
SUBMISSIONS = {}
SUBMISSION_QUEUE = None
TEST_SCRIPTS_DIRECTORY = None
JOB_LOGS_DIRECTORY = None
DEFAULT_PARALLEL = None
DEFAULT_TIMEOUT = None
CONCURRENT_SUBMISSIONS = None
HTTP_SESSION = None
COMPILER_HUB_BASE_URL = ""
SPECFILE = 'spec.json'
DBFILE = None
RUNFILE = None
RETENTION_DAYS = None
ADVERTISE = None
PORT = None
TIME_STARTED = None
NAME = None
EXPORT_HOST = None
EXPORT_PORT = None

SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "timeout": {"type": "number"},
        "no_logs": {"type": "boolean"},
        "working_directory": {"type": "string"},
        "uploads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "test_system": {"type": "string"},
                    "test_name": {"type": "string"},
                    "results_file": {"type": "string"}
                },
                "required": ["test_system", "test_name", "results_file"]
            }
        }
    },
    "required": ["parameters", "description"]
}

SUBMISSION_SCHEMA = {
    "type": "object",
    "properties": {
        "parallel": {"type": "number"},
        "note": {"type": "string"},
        "job_specs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "params": {"type": "object"}
                },
                "required": ["name"]
            }
        }
    },
    "required": ["job_specs"]
}

#
# Configuration
#

def get_arguments():
    """
    Get arguments for the server from the command line.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--master", help="The compiler hub URL to reference as the master server.", default="http://cv-framework.nvidia.com")
    parser.add_argument("-P", "--port", help="Local port to run on", default="7913")
    parser.add_argument("-H", "--host", help="Local host to run on", default="0.0.0.0")
    parser.add_argument("-T", "--test_directory", type=str, help="Set directory to use for test scripts.", default="test_scripts")
    parser.add_argument("-j", "--job_logs", type=str, help="Set directory to use to store logs for jobs.", default="job_logs")
    parser.add_argument("-q", "--queue_size", type=int, help="Size of submission queue - this is the maximum number of submissions allowed.", default=20)
    parser.add_argument("-s", "--concurrent_submissions", type=int, help="Number of submissions to allow running concurrently", default=1)
    parser.add_argument("-p", "--parallel", type=int, help="Default number of parallel jobs to run in a submission. Can be overridden by a submission.", default=4)
    parser.add_argument("-t", "--job_default_timeout", type=int, help="Default timeout for individual jobs. Can be overriden per job spec.", default=3600)
    parser.add_argument("-r", "--retention", type=int, help="Number of days to retain submission and job data. After the alotted time, data and logs will be purged.", default=10)
    parser.add_argument("-c", "--clean", action="store_true", help="Clean up old jobs on startup")
    parser.add_argument("-a", "--advertise", type=float, help="Advertising interval in minutes (notifying the hub server that this satellite is alive). An interval <= 0 turns off advertising.", default=10)
    parser.add_argument("-n", "--name", type=str, help="A short name to help identify this satellite", default=socket.gethostname())
    parser.add_argument("-d", "--dbfile", type=str, help="File used to persist job and submission metadata to disk.", default="satellite.db")
    parser.add_argument("-e", "--export-host", type=str, help="The host name to export to connect to this satellite instance", default=socket.gethostname())
    parser.add_argument("-E", "--export-port", type=str, help="The port to export to connect to this satellite instance")
    parser.add_argument("-S", "--submission", type=str, action="append", help="Initial submission file to run on startup. Multiple submissions can be specified here.")
    return parser.parse_args()

#
# Communicate with the Compiler Hub
#

async def hub_req(path, method, **kwargs):
    """
    Make a generic HTTP request to the hub (master)
    """
    request_id = make_id()
    fullpath = COMPILER_HUB_BASE_URL + path
    print(f'making HTTP {method} request to {fullpath} (id={request_id})')
    try:
        async with HTTP_SESSION.post(fullpath, headers={'X-Request-Id': request_id}, **kwargs) as res:
            if res.status != 200:
                text = await res.text()
                print(f'HTTP {method} (id={request_id}) to {fullpath} failed (status={res.status}): {text}')
            else:
                print(f'HTTP {method} (id={request_id}) to {fullpath} succeeded')
                return await res.json()
    except asyncio.CancelledError:
        pass
    except asyncio.TimeoutError:
        pass

async def hub_post(path, data, **kwargs):
    """
    Make a post to compiler hub.
    """
    return await hub_req(path, 'post', json=data, **kwargs)

async def hub_get(path, **kwargs):
    """
    Make a get request for JSON data from the compiler hub.
    """
    return await hub_req(path, 'get', **kwargs)

#
# Test Script Specifications
#

def load_spec(test):
    """
    Load a JSON file (given a test) and check it against a schema.
    """
    specpath = os.path.join(TEST_SCRIPTS_DIRECTORY, test, SPECFILE)
    with open(specpath) as specfile:
        data = json.load(specfile)
        jsonschema.validate(instance=data, schema=SPEC_SCHEMA)
        return data

async def process_spec(name, spec):
    """
    Given a loaded spec, we may need to process it and run various subprocesses to
    get dynamic, available parameter options.
    """
    for param in spec["parameters"]:
        if "shell" not in param:
            continue
        shell = param["shell"]
        proc = await asyncio.create_subprocess_shell(
            shell,
            cwd=os.path.join(TEST_SCRIPTS_DIRECTORY, name),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        try:
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                # Filter to remove empty lines
                opts = param.get("options", []) + list(filter(lambda x: x, stdout.decode().splitlines()))
                param["options"] = opts
            else:
                param["options"] = []
        except asyncio.CancelledError:
            param["options"] = []
    return spec

def get_available():
    """
    Get available tests to run by looking inside the test_scripts directory.
    """
    valid = []
    invalid = []
    for entry in os.scandir(TEST_SCRIPTS_DIRECTORY):
        name = entry.name
        try:
            valid.append({
                "name": name,
                "spec": load_spec(name)
            })
        except jsonschema.ValidationError as e:
            invalid.append({
                "name": name,
                "error": str(e)
            })
        except NotADirectoryError:
            pass
    return {"valid": valid, "invalid": invalid}

async def advert(interval_minutes):
    """
    Notify the hub that this satellite is running periodically while the satellite is running.
    """
    seconds = interval_minutes * 60
    if seconds <= 0:
        return
    while True:
        await hub_post('/api/satellite/advertise', wrap_body({"ttl": 2 * seconds, 'info': get_available()}))
        await asyncio.sleep(seconds)

async def unadvert():
    """
    Notify the hub that this satellite is terminating.
    """
    print('notifying master that this satellite is terminating, will timeout after 15 seconds')
    res = await hub_post('/api/satellite/unadvertise', wrap_body({}), timeout=ClientTimeout(total=15))
    if not res:
        print('notifying master timed out')

#
# Purging Data
#

def vacuum():
    """
    Remove jobs that are older than 10 days so the JOBS dict does not grow forever.
    Also remove old submissions.
    """
    earliest = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
    for sub in list(SUBMISSIONS.values()):
        if sub["status"] != "DONE":
            continue
        if sub["_submitted"] >= earliest:
            continue
        # Remove submission
        del SUBMISSIONS[sub['submission_id']]
    for job in list(JOBS.values()):
        if job["status"] == "PENDING":
            continue
        if job["_submitted"] >= earliest:
            continue
        # Remove job and logs
        del JOBS[job['job_id']]
        shutil.rmtree(os.path.join(JOB_LOGS_DIRECTORY, str(job['job_id'])), ignore_errors=True)

#
# Spawning Jobs
#

def sorted_jobs():
    """
    Get a list of jobs, sorted with most recent first.
    """
    return sorted(JOBS.values(), key=lambda x: x["_submitted"], reverse=True)

def sorted_submissions():
    """
    Get a list of submissions, sorted with most recent first.
    """
    return sorted(SUBMISSIONS.values(), key=lambda x: x["_submitted"], reverse=True)

def make_id():
    """
    Create a job id.
    """
    return urlsafe_b64encode(uuid.uuid4().bytes)[0:22].decode()

def unpack_record(record):
    """
    Convert a record (submission or job) to a value that can be serialized to JSON.
    """
    return {k: v for k, v in record.items() if not k.startswith('_')}

def job_dir(job_id):
    """
    Get the directory that contains job information and logs.
    """
    return os.path.join(JOB_LOGS_DIRECTORY, str(job_id))

def open_job_log(logname, job):
    """
    Open a writeable file for a log
    """
    dirpath = job_dir(job['job_id'])
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath, f'{logname}.log')
    return open(filename, "wb")

def queue_job(submission_id, name, params, now,  jid=None):
    """
    Create and queue a job. The new job will be in the pending state.
    """
    job_id = jid or make_id()
    job = {
        "name": name,
        "params": params,
        "submitted": str(now),
        "_submitted": now,
        "job_id": job_id,
        "submission_id": submission_id,
        "status": "PENDING",
    }
    JOBS[job_id] = job
    return job

async def start_job(job):
    """
    Start a job (the job should be queued). Returns async when job finishes.
    """
    # Check if canceled
    if job['status'] != 'PENDING':
        return
    # Basic info
    job_id = job['job_id']
    name = job['name']
    print(f'job {name} ({job_id}) started.')
    # Get specs for job
    specs = load_spec(job['name'])
    # Convert param map to arguments list
    cli_args = ["--" + str(k) + "=" + str(v) for k, v in job['params'].items()]
    # Build environment table
    envdict = {
        **dict(os.environ),
        "JOB_ID": job['job_id'],
        "SUBMISSION_ID": job['submission_id'],
        "TEST_SCRIPTS_DIRECTORY": os.path.abspath(TEST_SCRIPTS_DIRECTORY),
        "JOB_LOGS_DIRECTORY": os.path.abspath(JOB_LOGS_DIRECTORY),
        "COMPILER_HUB_BASE_URL": COMPILER_HUB_BASE_URL,
        "LOGDIR": os.path.abspath(os.path.join(JOB_LOGS_DIRECTORY, job_id))
    }
    for k, v in job['params'].items():
        envdict['arg_' + str(k)] = str(v)
    # Run test in subprocess
    logdir = job_dir(job_id)
    os.makedirs(logdir, exist_ok=True)
    workdir = specs.get("working_directory", logdir)
    if specs.get("no_logs"):
        proc_stdout = asyncio.subprocess.DEVNULL
        proc_stderr = asyncio.subprocess.DEVNULL
    else:
        proc_stdout = open_job_log('stdout', job)
        proc_stderr = open_job_log('stderr', job)
    proc = await asyncio.create_subprocess_exec(
        os.path.join(TEST_SCRIPTS_DIRECTORY, job['name'], 'run'),
        *cli_args,
        cwd=workdir,
        env=envdict,
        stdout=proc_stdout,
        stderr=proc_stderr)
    # Keep track of job
    now = datetime.datetime.utcnow()
    job["_proc"] = proc
    job["started"] = str(now)
    job["status"] = 'RUNNING'
    # Wait for job
    timeout = specs.get('timeout', DEFAULT_TIMEOUT)
    try:
        return_code = await asyncio.wait_for(proc.wait(), timeout=timeout)
        # Job may have been canceled
        if job['status'] == 'RUNNING':
            job["status"] = 'DONE' if return_code == 0 else 'ERROR'
        job["return_code"] = return_code
    except asyncio.TimeoutError:
        proc.terminate()
        job["status"] = "TIMEOUT"
    except asyncio.CancelledError as e:
        proc.terminate()
        pass
    job["finished"] = str(datetime.datetime.utcnow())
    print(f'job {name} ({job_id}) finished with status {job["status"]}.')
    # Close log files
    if not specs.get("no_logs"):
        proc_stdout.close()
        proc_stderr.close()
    del job["_proc"]
    # Don't upload anything from failed job (we still keep the artifacts, but we don't pollute test results)
    if job["status"] != "DONE":
        return
    # Submit test results on behalf of the script.
    for upload in specs.get('uploads', []):
        try:
            results_file = upload.get('results_file')
            test_name = upload.get('test_name')
            test_system = upload.get('test_system')
            full_file_path = os.path.join(workdir, results_file)
            if results_file.endswith('.csv'):
                print(f'warning: csv data uploads not yet implemented (results_file={results_file})')
                return
            with open(full_file_path) as results:
                data = json.load(results)
            print(f'uploading test results to {test_system}.{test_name} for job {job_id}.')
            asyncio.ensure_future(hub_post(f'/api/results/push/{test_system}/{test_name}', data))
        except FileNotFoundError:
            print(f'ignoring upload {results_file} for job {job_id}, file not found')

def cancel_job(job):
    """
    Try to cancel a job. Returns True if the jobs was canceled, False otherwise.
    """
    if job['status'] == 'PENDING':
        job['status'] = 'CANCELED'
        return True
    elif job['status'] == 'RUNNING':
        job['status'] = 'INTERRUPTED'
        job['_proc'].terminate()
        return True
    else:
        return False

#
# Submission Queue
#

def queue_submission(specs, parallel, note, ts=None, sid=None, jids=None):
    """
    Queue a set of jobs for execution. Returns None if could not queue.
    Optionally takes some parameters like a timestamp, a submission id, and
    a list of job ids. This lets a serialized submissions be "resubmitted"
    on startup in case the satellite goes down and we want to restart the running jobs.
    """
    # Check if queue is full
    if SUBMISSION_QUEUE.full():
        return None
    sub_id = sid or make_id()
    now = ts or datetime.datetime.utcnow()
    # Supply job ids if the are provided. This happens if this submission comes from the DBFILE.
    if jids:
        jobs = [JOBS.get(jids[i]) or queue_job(sub_id, spec.get('name'), spec.get('params', {}), now, jid=jids[i]) for i, spec in enumerate(specs)]
    else:
        jobs = [queue_job(sub_id, spec.get('name'), spec.get('params', {}), now) for spec in specs]
    submission = {
        "submission_id": sub_id,
        "parallel": parallel,
        "_specs": specs,
        "_submitted": now,
        "submitted": str(now),
        "status": "PENDING",
        "note": note,
        "_jobs": jobs,
        "num_jobs": len(jobs),
        "job_ids": [x["job_id"] for x in jobs]
    }
    # Queue is not full, will not error.
    SUBMISSION_QUEUE.put_nowait(submission)
    SUBMISSIONS[sub_id] = submission
    print(f'submission ({sub_id}) queued with {len(specs)} jobs.')
    return submission

async def do_submissions():
    """
    Execute submissions forever. This gets started in an async task at server
    start and runs in the background.
    """
    while True:
        submission = await SUBMISSION_QUEUE.get()
        try:
            jobs = submission["_jobs"]
            job_iter = iter(jobs)
            parallel = submission.get("parallel", DEFAULT_PARALLEL)
            task_count = min(len(jobs), max(parallel, 1))
            # Pop jobs from job iterator until none left.
            async def executor():
                for job in job_iter:
                    await start_job(job)
            # Run jobs N-way parallel
            sub_id = submission['submission_id']
            print(f'submission ({sub_id}) started ({task_count} way parallel).')
            submission['status'] = 'RUNNING'
            await asyncio.gather(*[executor() for _ in range(task_count)])
            # Submission finished
            print(f'submission ({sub_id}) finished.')
            # Submission may have been canceled
            if submission['status'] == 'RUNNING':
                submission['status'] = 'DONE'
        except asyncio.CancelledError as e:
            # If cancelled from signal, just finish.
            return
        except Exception as e:
            submission['status'] = 'ERROR'
            submission['error'] = str(e)
            traceback.print_exc()
        SUBMISSION_QUEUE.task_done()

#
# Routes
#

def wrap_body(body):
    """
    Wrap response body with common keys
    """
    ret = {
        "timestamp": str(datetime.datetime.utcnow()),
        "version": VERSION,
        'name': NAME or '',
        "satellite_port": EXPORT_PORT,
        "data": body
    }
    if EXPORT_HOST:
        ret['satellite_host'] = EXPORT_HOST
    return ret

def make_response(body, **kwargs):
    """
    Create a response and wrap the body with some common information returned from all requests.
    """
    # Use custom json.dumps to make response look prettier in plain text.
    return web.json_response(wrap_body(body),
        dumps=lambda x: json.dumps(x, indent=2) + "\n",
        headers={'Access-Control-Allow-Origin': "*"},
        **kwargs)

async def route_info(_):
    """
    Get basic info about the service. Also can be used as a health check.
    """
    total, used, free = shutil.disk_usage('/')
    return make_response({
        'master': COMPILER_HUB_BASE_URL,
        'name': NAME or '',
        'test_scripts': TEST_SCRIPTS_DIRECTORY,
        'job_logs': JOB_LOGS_DIRECTORY,
        'default_parallel': DEFAULT_PARALLEL,
        'default_timeout': DEFAULT_TIMEOUT,
        'retention_days': RETENTION_DAYS,
        'concurrent_submissions': CONCURRENT_SUBMISSIONS,
        'advertise': ADVERTISE,
        'satellite_port': PORT,
        'num_jobs': len(JOBS),
        'num_submissions': len(SUBMISSIONS),
        'uptime': str(datetime.datetime.utcnow() - TIME_STARTED),
        'disk_total': total,
        'disk_used': used,
        'disk_free': free
    })

async def route_available(_):
    """
    Get all available tests we can launch.
    """
    return make_response(get_available())

async def route_spec(request):
    """
    Get the processed spec for a single test script (shell commands expanded).
    """
    name = str(request.match_info['testname'])
    try:
        spec = load_spec(name)
    except FileNotFoundError:
        return make_response('Not found', status=404)
    return make_response(await process_spec(name, spec))

async def route_run(request):
    """
    Run tests on the server.
    """
    post = await request.json()
    try:
        jsonschema.validate(instance=post, schema=SUBMISSION_SCHEMA)
    except jsonschema.ValidationError as e:
        return make_response({"echo": post, "error": str(e.message)})
    specs = post.get('job_specs')
    parallel = post.get('parallel', DEFAULT_PARALLEL)
    note = post.get('note', '')
    submission = queue_submission(specs, parallel, note)
    if not submission:
        # Failed to schedule
        return make_response({
            "error": "submission queue full - try again later."
        }, status=400)
    # Everytime we add new jobs or submission, clean up.
    vacuum()
    return make_response({
        "submission_id": submission["submission_id"],
        "job_ids": [x['job_id'] for x in submission['_jobs']]
    })

async def route_jobs(_):
    """
    Get list of past and current jobs
    """
    jobs = [unpack_record(record) for record in sorted_jobs()]
    return make_response(jobs)

async def route_jobs_with_status(request):
    """
    Get list of past and current jobs with a specific status
    """
    status = request.match_info.get('status', 'RUNNING').upper()
    jobs = [unpack_record(record) for record in sorted_jobs() if record['status'] == status]
    return make_response(jobs)

async def route_jobs_in_range(request):
    """
    Get a list of jobs from a slice. Used for efficient pagination.
    """
    min_index = int(request.match_info.get('min'))
    max_index = int(request.match_info.get('max'))
    job_slice = sorted_jobs()[min_index:max_index]
    jobs = [unpack_record(record) for record in job_slice]
    return make_response({"total": len(JOBS), "slice": jobs})

async def route_submissions(_):
    """
    Get list of submissions.
    """
    subs = [unpack_record(record) for record in sorted_submissions()]
    return make_response(subs)

async def route_submissions_with_status(request):
    """
    Get list of submissions with a given status
    """
    status = request.match_info.get('status', 'RUNNING').upper()
    subs = [unpack_record(record) for record in sorted_submissions() if record['status'] == status]
    return make_response(subs)

async def route_submissions_in_range(request):
    """
    Get a list of submissions from a slice. Used for efficient pagination.
    """
    min_index = int(request.match_info.get('min'))
    max_index = int(request.match_info.get('max'))
    sub_slice = sorted_submissions()[min_index:max_index]
    subs = [unpack_record(record) for record in sub_slice]
    return make_response({"total": len(SUBMISSIONS), "slice": subs})

async def route_one_job(request):
    """
    Get information on a single job
    """
    job = JOBS.get(request.match_info['job_id'])
    if not job:
        return make_response("Not Found", status=404)
    rec = unpack_record(job)
    # Scan for job logs
    try:
        logs = []
        for entry in os.scandir(job_dir(job['job_id'])):
            name = entry.name
            logs.append(name)
        rec['logs'] = logs
    except FileNotFoundError:
        pass
    return make_response(rec)

async def route_one_job_log(request):
    """
    Get a log file for a given job.
    """
    job = JOBS.get(request.match_info['job_id'])
    if not job:
        return make_response("Not Found", status=404)
    path = os.path.join(job_dir(job['job_id']), request.match_info['logfile'])
    try:
        size = os.stat(path).st_size
        if size > 100 * 1024:
            return make_response({"status": "error", "error": "File too large, see raw"}, status=400)
        with open(path, 'r') as f:
            return make_response(f.read())
    except FileNotFoundError:
        return make_response("Not Found", status=404)

async def route_one_job_lograw(request):
    """
    Get a log file for a given job as a normal file (not JSON).
    """
    job = JOBS.get(request.match_info['job_id'])
    logfile = request.match_info['logfile']
    if not job:
        return make_response("Not Found", status=404)
    path = os.path.join(job_dir(job['job_id']), logfile)
    downloaded_filename = str(job['job_id']) + '.' + logfile
    try:
        return web.FileResponse(path, headers={"Content-Disposition": 'filename="' + downloaded_filename + '"'})
    except FileNotFoundError:
        return make_response("Not Found", status=404)

async def route_one_submission(request):
    """
    Get information on a single submission
    """
    sub = SUBMISSIONS.get(request.match_info['sub_id'])
    if not sub:
        return make_response("Not Found", status=404)
    return make_response(unpack_record(sub))

async def route_one_submission_jobs(request):
    """
    Get information on a single submission
    """
    sub = SUBMISSIONS.get(request.match_info['sub_id'])
    if not sub:
        return make_response("Not Found", status=404)
    jobs = [unpack_record(job) for job in sub['_jobs']]
    return make_response(jobs)

async def route_cancel_job(request):
    """
    Cancel a job.
    """
    job = JOBS.get(request.match_info['job_id'])
    if not job:
        return make_response("Not Found", status=404)
    if not cancel_job(job):
        return make_response("Could not cancel job", status=400)
    return make_response({})

async def route_cancel_submission(request):
    """
    Cancel a submission.
    """
    sub = SUBMISSIONS.get(request.match_info['sub_id'])
    if not sub:
        return make_response("Not Found", status=404)
    if sub['status'] == 'PENDING':
        sub['status'] = 'CANCELED'
    elif sub['status'] == 'RUNNING':
        sub['status'] = 'INTERRUPTED'
    else:
        return make_response("Could not cancel submission", status=400)
    for job in sub['_jobs']:
        cancel_job(job)
    return make_response({})

#
# Main
#

async def do_before(app, args=get_arguments()):
    """
    Tasks that will run before the server starts.
    """
    global JOBS
    global SUBMISSIONS
    global HTTP_SESSION
    global COMPILER_HUB_BASE_URL
    global TEST_SCRIPTS_DIRECTORY
    global JOB_LOGS_DIRECTORY
    global SUBMISSION_QUEUE
    global DEFAULT_PARALLEL
    global DEFAULT_TIMEOUT
    global RETENTION_DAYS
    global CONCURRENT_SUBMISSIONS
    global ADVERTISE
    global PORT
    global TIME_STARTED
    global NAME
    global DBFILE
    global EXPORT_HOST
    global EXPORT_PORT
    HTTP_SESSION = ClientSession()
    COMPILER_HUB_BASE_URL = args.master
    TEST_SCRIPTS_DIRECTORY = os.path.abspath(args.test_directory)
    JOB_LOGS_DIRECTORY = os.path.abspath(args.job_logs)
    SUBMISSION_QUEUE = asyncio.Queue(maxsize=args.queue_size)
    DEFAULT_PARALLEL = args.parallel
    DEFAULT_TIMEOUT = args.job_default_timeout
    RETENTION_DAYS = args.retention
    CONCURRENT_SUBMISSIONS = args.concurrent_submissions
    ADVERTISE = args.advertise
    PORT = args.port
    NAME = args.name
    TIME_STARTED = datetime.datetime.utcnow()
    EXPORT_PORT = args.export_port or PORT
    EXPORT_HOST = args.export_host
    # Load from persisted if available. Trust data integrity.
    DBFILE = shelve.open(args.dbfile, writeback=True)
    if not args.clean:
        SUBMISSIONS = DBFILE['SUBMISSIONS'] if 'SUBMISSIONS' in DBFILE else {}
        JOBS = DBFILE['JOBS'] if 'JOBS' in DBFILE else {}
        subs = DBFILE['SUBMISSION_QUEUE'] if 'SUBMISSION_QUEUE' in DBFILE else []
        for sub in subs:
            queue_submission(sub['specs'], sub['parallel'], sub.get('note', ''), ts=sub["submitted"], sid=sub["submission_id"], jids=sub["job_ids"])
    # Print start up info as early as possible for debugging.
    print(f'setting up hub satellite on {args.host}:{args.port}')
    print(f'  name                    : {NAME or ""}')
    print(f'  master                  : {COMPILER_HUB_BASE_URL}')
    print(f'  queue size              : maximum {SUBMISSION_QUEUE.maxsize} pending submissions')
    print(f'  concurrent submissions  : maximum {CONCURRENT_SUBMISSIONS} running submissions')
    print(f'  parallel                : maximum {DEFAULT_PARALLEL} concurrent jobs per submission')
    print(f'  timeout                 : default {DEFAULT_TIMEOUT} seconds')
    print(f'  test directory          : {TEST_SCRIPTS_DIRECTORY}')
    print(f'  job log directory       : {JOB_LOGS_DIRECTORY}')
    print(f'  database file           : {args.dbfile}')
    print(f'  retention               : {RETENTION_DAYS} days')
    print(f'  export host             : {EXPORT_HOST}')
    print(f'  export port             : {EXPORT_PORT}')
    adstring = ' (off)' if ADVERTISE <= 0 else ''
    print(f'  advertising interval    : {ADVERTISE} minutes{adstring}')
    # Check if test directory exists
    if not os.path.isdir(TEST_SCRIPTS_DIRECTORY):
        print(f'Directory {TEST_SCRIPTS_DIRECTORY} does not exist. Perhaps you should create it?')
        sys.exit(1)
    # Clean old jobs
    if args.clean:
        shutil.rmtree(JOB_LOGS_DIRECTORY, ignore_errors=True)
    # Add initial submissions
    for sub in (args.submission or []):
        try:
            print(f'queueing initial submission {sub}')
            with open(sub) as f:
                sub_data = json.load(f)
                queue_submission(sub_data['job_specs'], sub_data.get('parallel', DEFAULT_PARALLEL), sub_data['note'])
        except Exception:
            print(f'failed to queue initial submission {sub}')
    # Start some background tasks
    loop = asyncio.get_event_loop()
    for _ in range(CONCURRENT_SUBMISSIONS):
        loop.create_task(do_submissions())
    loop.create_task(advert(ADVERTISE))

async def do_after(_):
    """
    Clean up from the main run.
    """
    # Clean running and pending jobs for integrity
    for jid, job in list(JOBS.items()):
        if "_proc" in job:
            del job["_proc"]
        if job["status"] == "PENDING" or job["status"] == "RUNNING":
            del JOBS[jid]
            shutil.rmtree(os.path.join(JOB_LOGS_DIRECTORY, str(jid)), ignore_errors=True)
    # Clean submissions and create queue for restarting submissions
    pending_subs = []
    for sid, sub in list(SUBMISSIONS.items()):
        if sub["status"] == "PENDING" or sub["status"] == "RUNNING":
            pending_subs.append({
                "parallel": sub["parallel"],
                "specs": sub["_specs"],
                "submitted": sub["_submitted"],
                "submission_id" : sub["submission_id"],
                "job_ids" : sub["job_ids"]
            })
            del SUBMISSIONS[sid]
    DBFILE["JOBS"] = JOBS
    DBFILE["SUBMISSIONS"] = SUBMISSIONS
    DBFILE["SUBMISSION_QUEUE"] = pending_subs
    # close and sync to disk
    DBFILE.close()
    # Try and tell master that we are terminating and close HTTP client
    await unadvert()
    await HTTP_SESSION.close()

def main(arguments):
    """
    Run with argparse configuration.
    """
    app = web.Application(middlewares=(
        cors_middleware(allow_all=True),
        error_middleware()
    ))
    app.add_routes([web.get('/info', route_info),
                    web.get('/available_tests', route_available),
                    web.get('/spec/{testname}', route_spec),
                    web.post('/run', route_run),
                    web.get('/jobs', route_jobs),
                    web.get('/jobs/{status}', route_jobs_with_status),
                    web.get('/jobs/range/{min}/{max}', route_jobs_in_range),
                    web.get('/submissions', route_submissions),
                    web.get('/submissions/{status}', route_submissions_with_status),
                    web.get('/submissions/range/{min}/{max}', route_submissions_in_range),
                    web.get('/job/{job_id}', route_one_job),
                    web.get('/job/{job_id}/log/{logfile}', route_one_job_log),
                    web.get('/job/{job_id}/lograw/{logfile}', route_one_job_lograw),
                    web.get('/submission/{sub_id}', route_one_submission),
                    web.get('/submission_jobs/{sub_id}', route_one_submission_jobs),
                    web.post('/cancel_job/{job_id}', route_cancel_job),
                    web.post('/cancel_submission/{sub_id}', route_cancel_submission)])
    app.on_startup.append(do_before)
    app.on_cleanup.append(do_after)
    web.run_app(app, port=arguments.port, reuse_port=True, host=arguments.host, reuse_address=True, print=None)

if __name__ == '__main__':
    main(get_arguments())