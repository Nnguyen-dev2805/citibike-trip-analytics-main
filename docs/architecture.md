# Lakehouse Architecture

This project implements a local Data Lakehouse for NYC Citi Bike trip analytics. It uses Docker containers instead of paid cloud services, and MinIO replaces AWS S3 as the object storage layer.

## Layer Mapping

| Course layer | Implementation | Role |
|---|---|---|
| Ingestion Layer | Python downloader + Spark Bronze job | Download official Citi Bike files and load raw CSV records |
| Storage Layer | MinIO | Store raw files and Delta tables in a local S3-compatible bucket |
| Table Format Layer | Delta Lake | Provide ACID transactions, schema handling, and versioned table storage |
| Processing Layer | Apache Spark / PySpark | Clean, transform, validate, and aggregate trip data |
| Serving / Analytics Layer | Spark SQL, Trino, Superset | Query Gold tables and build dashboards |

## Physical Layout

```text
lakehouse/
  raw/citibike/
  source-zips/citibike/
  bronze/citibike/
  silver/citibike/
  gold/citibike/
    gold_daily_rides/
    gold_hourly_demand/
    gold_top_start_stations/
    gold_top_end_stations/
    gold_user_type_behavior/
    gold_bike_type_usage/
    gold_station_od_pairs/
```

## Why Lakehouse

A Lakehouse combines low-cost object storage with table management features usually associated with data warehouses. In this project, raw CSV files are preserved, while cleaned and aggregated tables are stored as Delta Lake tables so analytics can be reproduced and queried consistently.

## Main Design Decisions

- MinIO is used because the course requires local execution and no paid cloud.
- Spark is used for ETL because Citi Bike data can grow to many millions of rows.
- Delta Lake is used for Bronze, Silver, and Gold to demonstrate ACID table storage.
- Gold tables are small, business-oriented tables suitable for SQL and dashboards.
- Trino and Superset are included for serving and BI, while Spark SQL remains the stable core query path for local demos.
