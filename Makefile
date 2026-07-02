SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: up up-full down restart logs init build download-data sample-data bronze silver gold pipeline query validate register-trino trino-cli clean check test test-local verify

up:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(COMPOSE) up -d --build minio spark-master spark-worker-1 spark-worker-2 jupyter

up-full:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(COMPOSE) --profile analytics up -d --build

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f --tail=200

init:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(COMPOSE) --profile tools run --rm minio-client

build:
	$(COMPOSE) build

download-data:
	$(COMPOSE) run --rm spark-driver python3 scripts/download_citibike_data.py

sample-data:
	$(COMPOSE) run --rm spark-driver python3 scripts/create_demo_data.py

bronze:
	$(COMPOSE) run --rm spark-driver spark-submit src/jobs/ingest_bronze.py

silver:
	$(COMPOSE) run --rm spark-driver spark-submit src/jobs/transform_silver.py

gold:
	$(COMPOSE) run --rm spark-driver spark-submit src/jobs/build_gold.py

pipeline:
	$(COMPOSE) run --rm spark-driver bash scripts/run_pipeline.sh

query:
	$(COMPOSE) run --rm spark-driver spark-submit src/jobs/query_gold.py

validate:
	$(COMPOSE) run --rm spark-driver spark-submit src/jobs/validate_lakehouse.py

register-trino:
	bash scripts/register_trino_tables.sh

trino-cli:
	$(COMPOSE) --profile analytics exec trino trino

check:
	bash scripts/check_services.sh

test:
	$(COMPOSE) run --rm spark-driver pytest -q

test-local:
	pytest -q

verify: up init sample-data pipeline validate test

clean:
	$(COMPOSE) down -v
	rm -rf data logs tmp checkpoints warehouse .pytest_cache
