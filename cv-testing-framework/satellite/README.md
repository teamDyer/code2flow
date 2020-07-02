# Compiler Hub satellite (cvcServer) (name pending)

The compiler hub satellite HTTP server and job scheduler. This is a small HTTP server can run scripts
on behalf of the Compiler Hub, the master server. Last updated  05-25-2020

The binary (called `satellite`) is a simple job scheduler and task runner for use with
the compiler hub. It is capable of receiving commands from the compiler hub server to run
jobs, scheduling those jobs, and uploading the results to the compiler hub server. The satellite itself
should be failry simple and agnostic to test contents, but knowledgable about the Compiler Hub.

## Concepts

### A submission

A collection of jobs sent by a user from the Compiler Hub.

### A job

A script invocation and parameters. This should be running some kind of test usually. Each
job is just a subprocess and associated metadata.

### Job Results

The results of a job are the test data that should be stored in the Compiler Hub database.
This data should be in JSON (or eventually CSV) format.

### Job Specification

A Job specification contains metdata on how a test is to be run. Things like the default timeout value,
test parameters, and working directory can be stored here.
The specification file (spec.json) is a file that lives next to the script that will actually run the test.

## Downloading

The satellite can be downloaded as a standalone binary from the Compiler Hub gitlab repository. There is
only a Linux x64 build available now for download from gitlab - other arhcitectures and operating systems would
need to build from source.

On the repo [main page](https://gitlab-master.nvidia.com/compiler-verification-graphics/cv-testing-framework), next to
the blue clone button, there is a download button that will allow downloading artifacts from CI. Click this to download
artifacts from the `build-satellite` job. If you do not see any artifacts, select the `hubsatellite` branch instead of the `master` branch.

Once downloaded and uncompressed, the archive should contain an executable file called `satellite` which can be run to start a hub satellite server.

## Getting Set Up

It is best to run the satellite on a machine with a static IP address or constantly addressable host name. This ensures that it is constantly accesible by
the compiler hub server.

On first invocation, the hub satellite should quickly exit and complain about a missing `test_scripts` directory. This directory (configurable via
cli arguments), is the location of all of the test scripts your instance of the satellite will support. The Compiler Hub will be able to launch jobs
with only the scripts that are specified in this directory.

The directory tree should look as follows:

```
test_scripts/
  my_test_1/
    run
    spec.json
  my_test_2/
    run
    spec.json
  ...
```

Each test script is a actually a directory, with a bin or script named `run`, and a file `spec.json` which contains metadata about the `run` file.
Allowed keys are specified in the `spec.json` file as follows.

### Format of spec.json

`spec.json` has several required keys and several optional keys.

#### Required Keys

- "description" : Some text that describes what this test script does.
- "parameters" : An array of objects, each of which describe a possible parameter to the script. For the possible formats for each object, see the example below.

#### Optional Keys

- "timeout" : How long to wait for this script to run before terminating it and giving the job a TIMEOUT status
- "no_logs" : A boolean that disables stdout.log and stderr.log when true.
- "working_directory" : A directory path to run the test script from. By default, the script is run from the logs directory, which is `job_logs/[JOB_ID]/`.
- "uploads" : An array of entires to try to upload to the Compiler Hub when the job finishes. Each entry is an object with keys "results_file", "test_system", and "test_name".

Various keys and options may be added as needed.

### Example spec.json

Below is an example spec for a test 'example'.
```
{
    "description": "Example test. Runs for 5 seconds and ignores its parameters.",
    "parameters": [
        {
            "name": "nvvm_version",
            "type": "choice",
            "doc": "Pick a version of nvvm",
            "optional": false,
            "options": [
                "9",
                "10",
                "11"
            ]
        },
        {
            "name": "test",
            "type": "choice",
            "doc": "Pick a compute test",
            "optional": false,
            "options": [
                "cudart",
                "cublas",
                "cudarnn"
            ]
        },
        {
            "name": "triage",
            "type": "choice",
            "doc": "What kind of job to run, whether it be a single run, a binary regression search, or something else",
            "optional": false,
            "options": [
                "single_run",
                "brs",
                "serial"
            ]
        }
    ]
}
```

### Parameter Types

The majority of complexity in a `spec.json` is in specifying parameters to the script. There are many different ways to constrain parameters, and
these need to be stronger and more flexible than a simple type or tag system. Every parameter needs a `"name"` key, a `"type"` key, and a `"doc"` key -
these are the name of the parameter, a enum the describes how the parameter will be presented in a UI, and a human readable text string describing what the
parameter does. Also, if a parameter is `"optional"`, it can be left unspecified in a submission. A `"default"` key specifies a default value for the parameter.
These keys are used for all parameter types.

```
{
  "name": "my_param_name_snake_case",
  "type": "string",
  "doc": "Human readable text here - this is an example parameter",
  "optional": false,
  "default": "cat!"
}
```

In addition to these keys, each type may use other to specify a UI. Based on user need, more types may be added on request, especially dynamic types or types
specific to Nvidia use cases. All

#### `"boolean"` type

Present a simple checkbox to the user. The `./run` script is passed arguments in the form of a string, either `True` or `False`.

#### `"string"` type

Get any string of input. A simple, one-line text box is presented to the user, and any freeform text is allowed.

#### `"text"` type

The same as the `"string"` type, although the user is given a text field, which is longer and should generally be used when expecting long or multiline input.

#### `"choice"` type

When the user can select one of a statically determined, finite number of choices, use the `"choice"` type. Valid choices must be specified in the `"options"` key.
If a `"shell"` option is provided, it will be executed dynamically (from the same directory as the `./run` script) to populate available options. The output of the
shell command is separated by line, and each line is used as an available option. Options determined in this way will be appended to statically defined options.


Extra keys:
```
{
  "options": [
    "option1",
    "option 2",
    "cat",
    "dog",
    "..."
  ],
  "shell": "ls /etc/animal_options"
}
```

#### `"integer"` type

Constrain input to valid integers. Due to JS and JSON limitations, integers should be in range `-2^53` to `2^53`.

Optional extra keys:
```
{
  "min": -10,
  "max": 10
}
```

#### `"nat"` type

Same as integer type, but constrained to non-negative integers. Min and max do not apply.

#### `"real"` type

Specify any real number (IEEE754 double).

Optional extra keys:
```
{
  "min": -10,
  "max": 10
}
```

#### `"some"` type

Similar to the choice type, but the user can choose any subset from the presented choices. If the `"no_duplicates"` key is true,
then the choices must be a strict subset. Otherwise, the user can return a multiset (multiple instances of the same value).
All values will be concatenated as a comma separated string before being passed to the `./run` script. If a `"shell"` option is provided, it
will be executed dynamically (from the same directory as the `./run` script) to populate available options.

Optional extra keys:
```
{
  "no_duplicates": true,
  "options": [
    "cat",
    "dog",
    "bird"
  ],
  "shell": "ls /etc/animals"
}
```

#### `"date"` type

Let the user pick a date with resolution to the day. This will be passed to the `./run` script as a string `yyyy-MM-dd`.

### How tests run

When the satellite receives a submission from the Compiler Hub, that submission is immediately added to a queue. The satellite server is constantly 
removing submissions off of the queue in the order they arrived, and executing the jobs in that submission. While submissions are executed serially (by default),
within a submission, jobs can be executed in parallel.

To run a test, the satellite server will invoke the `run` script with command line arguments, environment variables, and working directory
as specified by `spec.json` and the job parameters. Arguments are passed in the form `--key=value`, such that
the `run` script could be executed as `run --a=b --verbose=true --key1=value1 --key2=value2`. Also, an environment variable for
each argument will be set like `arg_a`, `arg_verbose`, `arg_key1`, and `arg_key2` to make shell scripting easier. Scripts can parse either the CLI
arguments or environment variables to write scripts. Most likely, existing scripts will need to be wrapped as it is likely that satellite will be unable
to interact with a custom CLI inteface (positional arguments, unix style flags, etc.).

### Script Environment Variables

The satellite also sets several environment variables on a per job basis in the test scripts.

- JOB_ID: Identifies the currently running job
- SUBMISSION_ID: Identifies the submission that started this job
- TEST_SCRIPTS_DIRECTORY: Absolute path to the directory where the test script came from. Default is $(satelliteWorkingDir)/test_scripts
- JOB_LOGS_DIRECTORY: Absolute path to the directory where all job logs are kept. Default is $(satelliteWorkingDir)/job_logs
- LOGDIR: Absolute path to directory where satellite will look for logs. Needed if job is running from an explicitly set directory.

More environment variables could be added based on user needs.

### Running the Satellite

Finally, once the test_script directory has been created, running `./satellite` will start a server. The `test_scripts` directory can be modified without restarting the server, allowing
one to add or modify tests. The `./satellite` binary takes many configuration options, which can be accessed though the `-h` flag.

In most cases, you probably want to set a nickname for the satellite for debugging, as well as advertise the current host this satellite is running on. Some useful options:

* `-n` set a nickname for the satellite
* `-m` set the master compiler hub instance for the satellite - by default is http://cv-framework.nvidia.com, but it could be http://chub-stage.nvidia.com for staging.
* `-e` set the export hostname fo this satellite. This is the hostname that the compiler hub will try and use to connect to this satellite. This can be an ip address
       or a hostname. This works best with a static ip address or a static hostname. The compiler hub will try to autodetect this, but it is best to supply this
       yourself.
 
```
./satellite -n sat-nickname -m http://chub-stage.nvidia.com -e my-computer.nvidia.com
```

## Web Interface

The main way to interact with the satellite is through the web interface, which will be located at `http://[COMPILER_HUB_HOST]/satellite`. This allows you to
to select one of the connected satellites, which you can inspect for jobs, submissions, and general information. There is also a form that will let you fill out
job submissions for a slave.

## satctl

For debugging, there is a local utility `satctl`. This simply connects to the local satellite server and lets you inspect jobs and submissions.
It is very minimal and does not do much more than wrap the HTTP api of the satellite. You need to have a running server to use satellitectl, usually
on your local machine, although you can specify a remote machine to work with via the `SATELLITE_URL` environment variable.

For example, to submit jobs, one can use `./satctl submit_file submission.json`, where submission.json is a file that describes a submission.

Example submission.json:

```
{
    "parallel": 3,
    "note": "example submission",
    "job_specs": [
        {"name": "example", "params": {"a": 1, "b": "is a test"}},
        {"name": "example", "params": {"a": 2, "b": "is a test"}},
        {"name": "example", "params": {"a": 3, "b": "is a test"}},
        {"name": "example", "params": {"a": 4, "b": "is a test"}},
        {"name": "example", "params": {"a": 5, "b": "is a test"}}
    ]
}
```

Result:

```
{
  "timestamp": "2020-05-26 17:07:22.844929",
  "version": "0.0.0",
  "data": {
    "submission_id": "kw0dZmh4R42lb2yZH7kGBA",
    "job_ids": [
      "DKDaB5I6SVmMk65hvZ-aaA",
      "dvRPJUm3TGKdBAU-i0yvOg",
      "piAPBATkQameRWy_em39Lw",
      "Nv_6ageqSfawNi9Yv8ErFg",
      "OEDwQypeQJGJlekND1d2vA"
    ]
  }
}
```

This example submission contains 5 jobs that run the `example` script, each with
a different set of parameters. The submission will run 3 jobs in parallel at a time.

All satellitectl invocations will print the returned JSON to stdout.

To see the current status/result of jobs, you can use `satctl job DKDaB5I6SVmMk65hvZ-aaA` to see the
status of the job.

```
{
  "timestamp": "2020-05-26 17:09:31.726968",
  "version": "0.0.0",
  "data": {
    "name": "example",
    "params": {
      "a": 1,
      "b": "is a test"
    },
    "submitted": "2020-05-26 17:07:22.844715",
    "job_id": "DKDaB5I6SVmMk65hvZ-aaA",
    "submission_id": "kw0dZmh4R42lb2yZH7kGBA",
    "status": "DONE",
    "started": "2020-05-26 17:07:22.911102",
    "return_code": 0,
    "finished": "2020-05-26 17:07:23.908788"
  }
}
```

All operations that can be done with satellitectl (and more) can also be done directly with the HTTP api.

## Concurrency and Parallelism

The satellite server is capable of handling many submissions and many jobs at once. Once
an alloted number of jobs and submissions are running, new submission and jobs will be
added to queues and set to a pending state. The satellite server does not do any complex scheduling
or resource allocation - for example, if multiple submitted jobs all require a certain machine, it is up
to the test script to put a mutex around the machine and only allow one job to run at the machine at a time.

This part of the system may be subject to change, but currently the satellite can run M submissions in parallel, and
each job can run N jobs in parallel. A submission can also override the value N to run fewer or more jobs in parallel.
There is currently no mechanism for resource allocation - i.e, no way to indicate that 2 jobs both use resource X (most likely a physical machine or GPU), such
that they should not run at the same time. To work around this, one job would need to wait until the first jobs finishes
so that X is available, or should immediately fail as X is not available.

Currently pending and running submissions and jobs can be retreived via the HTTP api and `satellitectl`.

## Data Persistence

The satellite is not meant to persist data for long periods of time, nor meant to allow complex queires over data. That said, the satellite
will store job artifacts and log files on disk for a period of time so that they can be accessed via the UI and SSH or other remote access.
a small database of jobs and submissions is also persisted to disk in the case where the satellite program is stopped, such as a machine being rebooted
or upgrading the satellite. When the satellite restarts, it will restart submissions and jobs that were interrupted by the stop. Data is stored in a local
database file, by default called `satellite.db`.

## Data Retension

The satellite is not meant to persist data for long periods of time. Any data that needs to be persisted should be uploaded
to either the compiler hub or to a drive. By default, all jobs are run in a newly created directory, and logs for 
stdout and stderr are saved in this directory. These logs will persist for sometime, until either the server is stopped
and then restarted (starting clears the old logs, so just stopping the server will not delete logs), or until they expire.
The default expiration time is 10 days. This will clear stdout/stderr logs as well as any other files that were written to the current
directory of the test script.

These intermediate files will be located in `./job_logs/{job_id}` for any given job.

## Autosubmission of Test results

The hub satellite also tries to make it easier to submit test results to the compiler hub for test owners.
In the `run_spec.json` file, one can specify various uploads to the compiler hub for result data. These files
will be automatically submitted to a compiler hub test table when a test completes. Currently, only JSON files
can be uploaded, although may need to be added.

For examples of this, look in the `/satellite/test_scripts/` directory.

## Examples

See example test scripts in the `/satellite/test_scripts/` directory in the repository. See sample submissions in the `/satellite/sample_submissions` directory.
