# CV Testing Framework

CV Testing Framework - a Web application for simplifying testing for the Compiler Verification Team.

## Setup for Local Development

As of January 2020, I do most of the development on Windows Subsystem for Linux, with Ubuntu 18.04. This is a much better approximation of
_real_ Ubuntu 18.04, our deployment environment, and in general works better than Cygwin. The caveat is that certain linux binaries
will not work in WSL (32 bit binaries, like VRL submit), and connecting to the compute team's box works best in non-WSL Ubuntu. This isn't a huge issue
right now for local development, and should be fixed in future versions of Linux for Windows.

If you are using WSL, you no longer need to install Cygwin.

Be sure to clone the repository in an Ubuntu terminal, not Git for Windows or another version of Git.

When pulling changes from upstream, you should usually be able to run `make setup` again to get new dependencies.

### VSCode

The editor I use to develop this application is VSCode. VSCode works well with many different languages, including python, but it also
has some of the best integration with Typescript and Angular, which is used on the frontend. It should be able to provide
an IDE-like experience for development for the backend and frontend at the same time. Install the Windows version of VSCode, which can
connect to the Linux file system on your device via an extension.

You can install VSCode directly from the [website](https://code.visualstudio.com/).

You should install several extensions for a good development experience.

- "Remote - WSL" - for connecting to Ubuntu.
- "Python" - for interacting with the Flask application

When Ubuntu is set up, you will be able to click the green icon in the bottom left corner, and
ceate an editor window that "mounts" the Ubuntu instance. This is an isolated filesystem. In the new window you created, you can click `Add workspace folder...`, and select `cv-testing-framework` as the new workspace folder. Once you do this, you should see the file tree of the git repository in your editor.

#### Running from within VSCode

VSCode offers an embedded terminal which makes working with the project easier. `Ctrl-\`` (control-tilde) opens an embedded terminal. You can use the spilt terminal feature to
run the frontend in one terminal, and the backend in another.

### Gitlab Setup and Cloning the Repository

The best way to use our Gitlab instance from and Ubuntu terminal is via an SSH key. This is an easy, password-less way to
interact with a remote git repository, muck like Perforce tickets.

In a browser, navigate to [https://gitlab-master.nvidia.com/profile/keys] to set up an SSH key (you may need to login or create an account).

Next, in an Ubuntu terminal:

```
ssh-keygen -t rsa -b 4096
cat ~/.ssh/id_rsa.pub
```

You can choose all of the default options given to you by `ssh-keygen`.

This will print your public key to the terminal. Copy this, and paste it into the Key field on the GitLab add key page. Give it a title and
click "Add key". You should now be able to clone the project via SSH in your Ubuntu terminal.

Lastly, to be able to push commits to GitLab, you need to set some git config options.

```
git config --global user.name "Calvin Rose"
git config --global user.email "crose@nvidia.com"
```

Once you have gitlab set up, you can clone the repository in your Ubuntu terminal (use the ssh url - this is what gets put
on your clipboard when you click "Clone with SSH").

```
git clone ssh://git@gitlab-master.nvidia.com:12051/compiler-verification-graphics/cv-testing-framework.git
```

### Ubuntu 18.04 on Windows (WSL) and setting up the Dev Environment

You can set up WSL and install Ubuntu 18.04 by following directions on the [Ubuntu website](https://wiki.ubuntu.com/WSL). Be sure
to install version 18.04 (Bionic). You may also want to download the Ubuntu installer from
[Microsoft's website](https://docs.microsoft.com/en-us/windows/wsl/install-manual) rather than the Windows store.

Install system dependencies, clone the project, and then install pipenv and run the setup script.

We need to use a node version that is relatively recent (I know that v12.13.0 works). After
installing `nodejs`, check the version with `node --version`.

If you have Node.js installed on Windows locally, you should remove it, as it interferes with Ubuntu's node.js.
You can also remove your Window's PATH from your Ubunutu PATH.

From an Ubuntu terminal:
```
# Get the correct version of node.
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt-get update                                                            # Update apt package listing
sudo apt-get upgrade                                                           # Install latest packages
sudo apt-get install python3 nodejs python3-pip redis-server postegresql       # Install python3, node, npm, pip3, redis, and postgres
sudo pip3 install pipenv                                                       # Install pipenv
sudo pip3 install git-pylint-commit-hook                                       # Install git-pylint-commit-hook
git clone ssh://git@gitlab-master.nvidia.com:12051/compiler-verification-graphics/cv-testing-framework.git
cd cv-testing-framework
cp git-pylint-commit-hook/pre-commit .git/hooks/pre-commit
make setup
```

If git clone failes, with a permission error, either you do not have permission to view the project, or there was an issue setting up
your SSH key.

### Working on the Frontend

The frontend is built with angular, but you need to use the correct version of angular. (The setup script should handle this).
If you want to use `ng` commands to generate components, for example, use `npx` as a prefix to use the version of angular CLI that
is used to build the project.

For example:

```
npx ng generate component thingy
```

### Working on the Backend

Keep in mid that the backend runs in a virtualenv. The virtual env will live in `backend/.venv` when created,
and VSCode is set to look here for autocomplete, linting, etc.

## Running Everything

In order to run a useable application, you will need to run both the frontend and the backend. This means
using two separate terminal windows, one for the backend, and one for the frontend. See the sections below.

Alternatively,
```
make run-frontend &
make run-backend
```

## Running the Frontend

Run `make run-frontend` from an Ubuntu terminal.
The frontend will be at `http://127.0.0.1:4200`.

## Running the Backend

Run `make run-backend` from an Ubuntu terminal.

Alternatively, use VSCode's built in debugger and the VSCode
python extension to debug the flask application. Choose the "Python: Main Backend (Flask)" option
to run in the debugger.

The backend will be at `http://127.0.0.1:8000`.

The `make` scripts should handle creating and using a Python virtualenv for you.
It will also put the virtual environment in a place where VSCode expects it so you can use
IDE-like features while developing. 

## Running the backend with a local Postgres

For running the backend against a local database, you must first install Postgres
on your WSL image if you have not already (this has been since added to the setup instructions).

```
sudo apt install postgresql
```

Next, run `make reinit-postgres` to setup tables and users in the local database. This will tear down the local
cluster and recreate it, losing any local data in the process. This is useful for testing and experimenting with the schema.
You will only need to do this once during setup, but you can re-run this any time if your local database goes into a bad state. _You should
also stop a running instance of the backend if you want to do this, as a running backend may prevent the cluster from being destroyed_.

If you make changes to the sql files that defined our database schema, you can run `make update-postgres` which will not
tear down the current cluster, but will still run the sql in backend/db_setup against the database.

Once the local database is setup, you wil want to populate with data. To scrape some historical data into test tables, run
`make local-backscrape`, which will scrape results for all scrapable tests from the last 10 days. This will take a while, so
run in a background process or in a separate terminal. You probably shouldn't run this very often, and you 
can skip this step if you don't want to look at test results.

Finally, use `make run-backend-localdb` to run the compiler hub backend locally and point to your local database. This is intended
for faster local development, with no danger of corrupting the production or staging database.
This will also generally feel snappier than using the production database because the local database is
closer to the backend and will respond quicker.

### Cannot connect to the backed

If the compiler hub cannot connect to the local database, then local database may not be running. You can ensure that the
database is running with `make update-postgres` or `sudo service start postgresql`.

## Local Tests on the Backend

Run `make run-backend-test` from an Ubuntu terminal.

This is for testing the flask app. The test code is in the `backend/tests` directory.

## Deployment

When the application is working well on a local machine, you may want to
deploy a version to the actual server. Deployment is done via Gitlab pipelines
and Docker (as of 2020-05-06). Pushes to the master branch on Gitlab will deploy
to staging, and pushes of tagged commits will deploy those commits to production.
We try to deploy to production once a week or so, but it is good to coordinate with people
giving demos or other events. Deploying will cause the servive to go offline for a few minutes
(as the old docker image is stopped and the new one is started - we do not have blue green deployments).
Deploying will update both the backend and frontend code, but will not affect the database.

Any deployment that fails tests will not be deployed, and it is the responsibility of the
commit owner to fix this. You should receive an email if your push fails tests.

For pushing to production, we use tags of the format `v{YYYY}-{MM}-{DD}`, indicating the date that
the commit was pushed. If multiple deploys to production happen on the same day, indicate a new version
by appending `.1`, `.2`, `.3`, etc. to the tag.

### Staging Deploy
```
git push origin master
```

### Production Deploy
```
git tag v2020-05-06
git push --tags origin master
```

You can see old deploys by either checking the gitlab website or use `git tag --list` to
see all tags.

To edit the deployment procedure, look in `.gitlab-ci.yml` for a description of our process. Also,
you may want to SSH into our test machine with `make ssh-test` to inspect or gitlab runner, which is responsible
for automating this CI. Documentation on this file and Gitlab CI in general can be found on [Gitlab's Website](https://docs.gitlab.com/ee/ci/).

## Logs

## Postgres Database

The postgres database that backs the site can be accessed at http://cv-framework.nvidia.com:5050 through a web interface.
This dashboard is useful for debugging and development, as well as a stop gap admin panel.
The login credentials for this dashboard will be handed out on a case by case basis.

### Table layout

The motivation for table layout of the database is the desire to be simple to
as reduce the need to do many JOINs when doing queries for analytics, but
flexible enough to handle extra columns for specific test and other
functionality. See the `cvf2` database for the currently working data.
Although this may make things less convenient for the framework maintainer,
it should be preferable for test owners, who could have more customized
tables for tests.

The "top most" table is the `test_meta` table, which describes meta data for
each test, such as the name, subsystem (VRL, ccv, etc.), scraper
configuration, and associated table name. Each test has it's own table that
is owned by the test. Within a certain test subsystem, many of these tables
may look similar, but any given test can have it's own columns. Test specific
tables are named like `{system}.{testname}`. For example, and APIC test table
would be `vrl.cv_apic_dx11_group004`. (We may want to put all APIC tests
under a single test table). This table will contained scraped and pushed data
from VRL, as well as any other test specific data (such as subtests) that is
added either by the scraper, or by the test on push operation.

### Adding a new test

Adding a new test involves adding a row to the `test_meta` table, and a
corresponding test table. If you want to copy the format of an existing
table, it's best to use Postgres's table inheritance feature, where one table
inherits from a base table. This makes it easy to maintain a collection of
similar tables. This is a bit involved right now (Jan 2020) and should be made easier.