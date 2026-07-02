# Superset Instructions

## Open Superset

URL: <http://localhost:8088>

Default login:

```text
username: admin
password: admin
```

## Add Trino Database

In Superset, go to Settings -> Database Connections -> + Database.

Use this SQLAlchemy URI:

```text
trino://user@trino:8080/delta/default
```

If the default Superset image does not include the Trino driver, build a custom Superset image with `trino` installed, or use Spark SQL query screenshots for the course demo.

## Register Delta Tables in Trino

Run:

```bash
make register-trino
```

The SQL equivalent is documented in:

```text
sql/trino_queries.sql
```

## Create Datasets

Add these tables as Superset datasets:

- `gold_daily_rides`
- `gold_hourly_demand`
- `gold_top_start_stations`
- `gold_top_end_stations`
- `gold_user_type_behavior`
- `gold_bike_type_usage`
- `gold_station_od_pairs`

## Build Dashboard

Use the chart plan in `dashboard/dashboard_design.md`.
