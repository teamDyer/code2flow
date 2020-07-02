from flask import Blueprint, jsonify, session, request
from subprocess import Popen, PIPE
from src.auth import auth_wrap
import os
import platform
import re

app = Blueprint('vrlsubmit', __name__)

#
# Routes
#

@app.route('options/<field>', methods=['POST'])
def get_submit_options(field):
    """
    Get available options for submitting a job. The post body should contain
    a partially complete options table, and this route will return a json array
    of options that can complete the field. This route may not return exhaustive or
    even any results, as it may prove difficult.
    """
    return jsonify({})

@app.route('submit', methods=['POST'])
@auth_wrap
def submit_job():
    options = request.json
    options["username"] = session["username"] 
    try:
        (ids, ok, errtext) = vrlsubmit(options)
        if not ok:
            return jsonify({"status": "error", "error": "VRL submission failed: " + errtext}), 400
        else:
            return jsonify(ids)
    except Exception as e:
        # Return only message string, not stack trace
        return jsonify({"status": "error", "error": "VRL submission failed: " + str(e)}), 400


def vrlsubmit(configuration):
    """
    Submit a vrl job base a configuration dictionary. The keys are as follows:
        "username" (-u flag)
        "server" (-s flag)
        "operatingsystem" (-o flag)
        "testname" (-t flag)
        "note" (-n flag, don't add extra quotes)
        "package" (-z flag)
        "response" (-r flag)
        "machine" (-m flag)
        "machinepool" (-l flag)

    machine takes precendence over machinepool, and both will not
    be used in the submission.

    returns tuple(list(vrlid), ok)
    """

    # Validate input
    missingParam = vrlSubmitValidate(configuration)
    if missingParam:
        raise Exception('option "' + missingParam + '" not received')
    
    # Check WSL
    versionText = None
    with open('/proc/version') as x:
        versionText = str(x.read())
    isWSL = "Microsoft" in versionText
    if isWSL:
        return ([], False, "vrlsubmit does not currently work on WSL.")

    # Check isolation mode
    # "Regular": "REGULAR",
    # "Binary Regression Search": "BRS",
    # "Serial Isolation Search": "SIS"
    isolation_mode = configuration["isolation_mode"]
    if isolation_mode == "BRS":
        print("Binary Regression Search Isolation mode")
        # To-Do
        return ([], False, "Isolation mode is not yet supported.")
    else:
        print("Regular Isolation mode and Serial Isolation mode")
        serials = []
        errtext = ""
        for cl in configuration["package_urls"]:
            response = vrlSubmitForCl(configuration, configuration["package_urls"][cl])
            if response[0]:
                result = response[1]
                # Check error
                if not result:
                    errtext = errtext+"vrlsubmit command did not return result for "+cl+"; "
                    print(errtext)
                    continue
                serialResult = getSerialsFromResult(result)
                if serialResult[0]:
                    serials = serials + serialResult[1]
                else:
                    errtext = errtext + serialResult[1] + " for " + cl + "; "
            else:
                errtext = errtext + response[1] + " for " + cl + "; "
        print(errtext)
        if not errtext:
            return(serials, True, '')
        return(serials, False, errtext)

def vrlSubmitForCl(configuration, package_url):
    cmd = "run/vrlsubmit"
    args = [cmd]
    print("In vrlSubmitForCl function : "+package_url)
    def add_arg(flag, option):
        if option in configuration:
            args.append(flag)
            args.append(configuration[option])
    add_arg("-s", "server")
    add_arg("-o", "operatingsystem")
    add_arg("-u", "username")
    add_arg("-t", "testname")
    # Setting package URL
    args.append("-z")
    args.append(package_url)
    add_arg("-n", "note")
    add_arg("-r", "response")
    if "machine" in configuration:
        add_arg("-m", "machine")
    else:
        add_arg("-l", "machinepool")

    # Subprocess popen (line buffered)
    result = None
    print("running vrl job: ", args)
    try:
        with Popen(args, bufsize=-1, stdout=PIPE, stderr=PIPE) as proc:
            all_results = proc.communicate()
            result = str(all_results[0], 'utf-8')
            err_result = str(all_results[1], 'utf-8')
            print("stderr: " + err_result)
            print("stdout: " + result)
            print("exit code: " + str(proc.returncode))
            if proc.returncode != 0:
                raise Exception(err_result or 'vrlsubmit executable returned non-zero exit code: ' + str(proc.returncode))
            print("finished!")
            return (True, result)
    except Exception as e:
        errtext = "Failed launching vrlsubmit: " + str(e)
        print(errtext)
        return (False, errtext)

# This function will validate input params provided to vrl submit
def vrlSubmitValidate(configuration):
    parameters = ["server", "operatingsystem", "username", "testname", "note", "package_urls"]
    for param in parameters:
        if not param in configuration or not configuration[param]:
            return param
    return ""

def getSerialsFromResult(result):
    pattern = re.compile(r'Submission accepted as job\(s\) (.*)')
    match = pattern.search(result)
    if not match:
        errtext = "pattern did not match: \"" + result + "\""
        print(errtext)
        return (False, errtext)
    serials = match[1].split(' ')
    return (True, serials)