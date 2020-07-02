# Database Setup (Postgres)

This direcxtory contains scripts necessary for the set up of a new database from a fresh Postgres installation, as
well as common tasks in the administration of our database.
This is needed for setup on mew machines, local testing, and reproducibility.

The scripts here should try and be idempotnent - that is they should have no effect if run on an already set up database
or a partially setup database. This will let us use these scripts to incremental upgrade our existing database (add new tables).

## create.py

This is the python script that connects to a database and creates tables and users for the compiler hub.
It takes arguments as environment variables to specify the how to connect to the postgres database and
how to set it up.

- COMPILER_HUB_DATABASE_CREDENTIALS: how to connect with psycopg2 to database - default is 'postgresql:///', which is the local cluster and default database.
- COMPILER_HUB_BACKEND_PASSWORD: the password for the 'backend' user. Defaults to 'iitsoi'.
- COMPILER_HUB_BACKEND_READONLY_PASSWORD: the password for the 'backend_readonly' user. Defaults to 'iitsoi'.

## init_local_postgres

This is a bash script that is invoked by make to help with local development. It wraps
create.py with a few other commands to tear down the current postgres and set up a new cluster.