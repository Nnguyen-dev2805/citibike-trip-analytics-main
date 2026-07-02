#!/usr/bin/env bash
set -euo pipefail

check_url() {
  local name="$1"
  local url="$2"
  if curl -fs "${url}" >/dev/null 2>&1; then
    echo "OK   ${name}: ${url}"
  else
    echo "WARN ${name}: cannot reach ${url}"
  fi
}

check_optional_url() {
  local name="$1"
  local url="$2"
  if curl -fs "${url}" >/dev/null 2>&1; then
    echo "OK   ${name}: ${url}"
  else
    echo "SKIP ${name}: optional service is not reachable; run make up-full if needed"
  fi
}

check_url "MinIO API" "http://localhost:${MINIO_API_PORT:-9000}/minio/health/live"
check_url "MinIO Console" "http://localhost:${MINIO_CONSOLE_PORT:-9001}"
check_url "Spark Master UI" "http://localhost:${SPARK_MASTER_WEB_PORT:-8080}"
check_url "Jupyter" "http://localhost:${JUPYTER_PORT:-8888}"
check_optional_url "Trino" "http://localhost:${TRINO_PORT:-8085}/v1/info"
check_optional_url "Superset" "http://localhost:${SUPERSET_PORT:-8088}/health"
