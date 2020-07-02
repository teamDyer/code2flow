# C Hub Web Backend

The Compiler Hub Backend is a flask application written primarily in Python 3, with a Postgres Database. Our 'production'
deployment of the backend can be found at cv-framework.nvidia.com/api/*, which exposes all of our REST HTTP routes. To see
a list of available HTTP routes, visit http://cv-framework.nvidia.com/api/site-map. 

In both production and development, the app is run with `gunicorn`, a python web server suitable for production.
This is served behind an NGINX proxy, which is also used to serve the application frontend.

## Code Layout

### `run/`

Shell scripts meant to wrap deployment and running of the server are in in the `run` directory. This also contains
binaries that the server needs to execute to run certain tasks, like the Linux `vrlsubmit` binary.

### `taskq/`

Many long running tasks in the backend, such as scraping data from VRL, checking what files are in binary drop, submitting jobs, are
done via [Celery](http://www.celeryproject.com), a job queue for Python. These tasks are defined in this directory, currently in a single
file tasks. Many of the tasks are run on a schedule, like with `cron`. These tasks often import code from the `src/` directory, and should be fairly
small. If these tasks are getting too large, you may want to move the code into the `src/` directory.

The tasks that are schedule to run periodically are defined in the `taskq/` directory, but their schedule is defined in `celeryconfig.py`.

### `src/`

This is where the majority of the backend code should be, including Flask code, HTTP routes, scraping logic, etc. This is NOT where HTML rendering
code is, as our application is a single page application. Instead, this flask app serves almost entirely JSON.

#### Flask Blueprints

The application is divided into subapps, using Flask's Blueprint feature, such as `/api/dvs/...`, `/api/results/...`, etc, which are defined
in files like `src/dvs.py` and `src/results.py` respectively. This is to compartmentalize functionality and make our application easier to navigate.

There are also a few other files of use:
- `auth.py` - Authentication decorator for our flask functions. Currently uses plain LDAP as of Jan 2020, which is of questionable security
- `connections.py` - Functions for getting a database connection. Connections are not cached in any way right now, so usually you will want
  to reuse your connection. Since our database and flask app are running on the physical box right now, this actually isn't a huge issue.
- `app.py` - The python entry point for our flask application. Mostly responsible for tying together the various subapps used in the project.

#### `src/scrapers/`

This directory contains code from scraping test result data from external test systems and storing what we want into our Postgres Database.
All classes defined here should be subclasses of the `src/scrapers/Scraper.py` class and register to a tag string in `src/scrapers/__init__.py`. Registering
a class here will let the framework assocaiate a given test in the Postgres database with a certain scraper to peridoically collect test results.

#### `src/binarydrop/`

This is were we currently have a parser to check what DVS packages are in binary drop. This is check periodically (once a day), and stored in out database so we can quickly
make queries for available changelists for a given package.
