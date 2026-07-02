#!/usr/bin/env bash
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose}"
SCHEMA="default"
BASE_LOCATION="s3://lakehouse/gold/citibike"

tables=(
  gold_daily_rides
  gold_hourly_demand
  gold_top_start_stations
  gold_top_end_stations
  gold_user_type_behavior
  gold_bike_type_usage
  gold_station_od_pairs
  gold_monthly_summary
)

trino_sql() {
  ${COMPOSE} --profile analytics exec -T trino trino --execute "$1"
}

trino_sql "CREATE SCHEMA IF NOT EXISTS delta.${SCHEMA}"

for table in "${tables[@]}"; do
  if trino_sql "SHOW TABLES FROM delta.${SCHEMA} LIKE '${table}'" 2>/dev/null | tr -d '"' | grep -qx "${table}"; then
    echo "OK ${table} already registered"
  else
    echo "Registering ${table}"
    trino_sql "CALL delta.system.register_table(schema_name => '${SCHEMA}', table_name => '${table}', table_location => '${BASE_LOCATION}/${table}')"
  fi
done

echo "Registered Trino Delta tables in delta.${SCHEMA}"
