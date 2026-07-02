# Demo Script: 7-10 Minutes

## 1. Introduce the topic

Tên đề tài: Thiết kế và triển khai Data Lakehouse chạy local bằng Docker để phân tích dữ liệu chuyến đi NYC Citi Bike.

Explain that MinIO replaces cloud S3, Spark handles ETL, Delta Lake stores tables, and Trino/Superset support analytics.

## 2. Start services

```bash
cp .env.example .env
make up
make init
```

Open:

- MinIO Console: <http://localhost:9001>
- Spark UI: <http://localhost:8080>

## 3. Show raw data ingestion

Fast demo:

```bash
make sample-data
```

Official data demo:

```bash
make download-data
```

In MinIO, show `lakehouse/raw/citibike/`.

## 4. Run Bronze

```bash
make bronze
```

Explain that Bronze preserves raw columns and adds metadata.

## 5. Run Silver

```bash
make silver
```

Explain data cleaning: timestamp casting, invalid-row filtering, trip duration, date/hour/weekend, and Haversine distance.

## 6. Run Gold

```bash
make gold
```

Show `lakehouse/gold/citibike/` in MinIO and list the Gold tables.

## 7. Run analytics

```bash
make query
make validate
```

Explain the analytics questions:

- Highest ride days
- Peak demand hours
- Top start/end stations
- Member vs casual behavior
- Bike type usage
- Weekend vs weekday behavior
- Common origin-destination pairs

## 8. Dashboard layer

Optional full-stack demo:

```bash
make up-full
make register-trino
```

Open Superset at <http://localhost:8088>. Login with `admin` / `admin`. Explain the dashboard design from `dashboard/dashboard_design.md`.

## 9. Close with Lakehouse mapping

Summarize the 5 layers:

- Ingestion: downloader + Bronze job
- Storage: MinIO
- Table format: Delta Lake
- Processing: Spark
- Serving: Spark SQL / Trino / Superset
