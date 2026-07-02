#!/usr/bin/env bash
set -euo pipefail

echo "Running Bronze ingestion..."
spark-submit src/jobs/ingest_bronze.py

echo "Running Silver transformation..."
spark-submit src/jobs/transform_silver.py

echo "Building Gold tables..."
spark-submit src/jobs/build_gold.py

echo "Showing Gold previews..."
spark-submit src/jobs/query_gold.py
