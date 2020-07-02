# Simple makefile for running dev related commands. This is used as a task runner
# rather than as a traditional Makefile.

# Make all make commands run in a single shell (bash)
.ONESHELL:
SHELL:=/bin/bash

# The remote machine to deploy on. This requires
# entering a password many times but works fairly well
# it sould be seemless with ssh keys.
REMOTE=cv-framework-01@10.20.168.102
TEST_REMOTE=comphub@comphub-test.nvidia.com
STAGE_REMOTE=comphub-stage@chub-stage.nvidia.com

# SSH into the test server when you want to have more fine grained control or things go south.
.PHONY: ssh-test
ssh-test:
	ssh $(TEST_REMOTE)

# SSH into staging server
.PHONY: ssh-stage
ssh-stage:
	ssh $(STAGE_REMOTE)

# SSH into the server when you want to have more fine grained control or things go south.
.PHONY: ssh
ssh:
	ssh $(REMOTE)

#
# Development
# You need these to work on the project on your local machine.
#

# Remove local postgres cluster and set it up again.
# This will cause you to lose all local data!
.PHONY: reinit-postgres
reinit-postgres:
	sudo -u postgres backend/db_setup/init_local_postgres

# Similar to reinit-postgres, but does not delete the current cluster.
.PHONY: update-postgres
update-postgres:
	sudo -u postgres backend/db_setup/update_local_postgres

# Populate the local database with scrapers. Be careful with running this
# often, as it can take a long time. Ideally, this is run after initializing the local
# database to populate it with lots of historical data. Will scrape data from the last 2 days.
.PHONY: local-backscrape
local-backscrape: local-backscrape-tests local-backscrape-bdrop

.PHONY: local-backscrape-tests
local-backscrape-tests:
	@cd backend; source db_setup/local_db_creds.sh; \
		pipenv run python -c 'import taskq.tasks; taskq.tasks.scrape_new(48*3600)'

.PHONY: local-backscrape-bdrop
local-backscrape-bdrop:
	@cd backend; source db_setup/local_db_creds.sh; \
		pipenv run python -c 'import taskq.tasks; taskq.tasks.binary_drop_scrape()'

.PHONY: setup-frontend
setup-frontend:
	cd frontend
	npm i

.PHONY: setup-backend
setup-backend:
	@if [[ "$$(pip -V)" == *.venv* ]]; then echo "Inside virtual env, exiting. You can leave env with 'deactivate'."; exit 1; fi
	cd backend
	LC_ALL=C.UTF-8 LANG=C.UTF-8 PIPENV_VENV_IN_PROJECT=1 pipenv install --python `which python3` --dev

.PHONY: setup-satellite
setup-satellite:
	@if [[ "$$(pip -V)" == *.venv* ]]; then echo "Inside virtual env, exiting. You can leave env with 'deactivate'."; exit 1; fi
	cd satellite
	LC_ALL=C.UTF-8 LANG=C.UTF-8 PIPENV_VENV_IN_PROJECT=1 pipenv install --python `which python3` --dev

# Setup a newly cloned repository for development
.PHONY: setup
setup: setup-frontend setup-backend setup-satellite
	$(MAKE) reinit-postgres

# Run the server backend
.PHONY: run-backend
run-backend:
	cd backend; pipenv run bash run/develop

.PHONY: run-backend-localdb
run-backend-localdb:
	cd backend; pipenv run bash run/local

.PHONY: run-backend-test
run-backend-test:
	@cd backend; pipenv run bash run/test

# Run the frontend.
.PHONY: run-frontend
run-frontend:
	@cd frontend; npm run start

# Run a local test instance of the satellite against the local instance of the backend.
.PHONY: run-satellite-local
run-satellite-local:
	@cd satellite; pipenv run ./satellite.py -m http://127.0.0.1:4200 -n local-satellite -S sample_submissions/example1.json

.PHONY: run-satellite-local-2
run-satellite-local-2:
	@cd satellite; pipenv run ./satellite.py -m http://127.0.0.1:4200 -P 8961 -j job_logs_2 -n local-satellite-2 -a 1 -d satellite.db

# Run a satellite on your local machine against the production c hub instance
.PHONY: run-satellite-stage
run-satellite-stage:
	@cd satellite; pipenv run ./satellite.py -m http://chub-stage.nvidia.com -j job_logs_stage -a 1 -d sat_stage.db