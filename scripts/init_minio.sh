#!/usr/bin/env sh
set -eu

BUCKET="${MINIO_BUCKET:-lakehouse}"

mc alias set local http://minio:9000 "${MINIO_ROOT_USER:-minioadmin}" "${MINIO_ROOT_PASSWORD:-minioadmin}"
mc mb --ignore-existing "local/${BUCKET}"

for prefix in raw/citibike source-zips/citibike bronze/citibike silver/citibike gold/citibike trino-metastore; do
  tmp_file="/tmp/.keep"
  touch "${tmp_file}"
  mc cp "${tmp_file}" "local/${BUCKET}/${prefix}/.keep" >/dev/null
done

echo "MinIO bucket initialized: ${BUCKET}"
