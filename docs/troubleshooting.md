# Troubleshooting

## Docker container not starting

Run:

```bash
docker compose ps
docker compose logs <service-name>
```

If ports are already used, edit `.env` and change ports such as `MINIO_CONSOLE_PORT`, `JUPYTER_PORT`, or `SUPERSET_PORT`.

For the most reliable classroom demo, start the core stack first:

```bash
make up
```

Start Trino and Superset only when you need the optional BI layer:

```bash
make up-full
```

## Spark cannot connect to MinIO

Check that MinIO is running and initialized:

```bash
make init
docker compose logs minio
```

Verify these values in `.env`:

```text
MINIO_ENDPOINT=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

## Delta package version mismatch

This project uses Spark 3.5.1 and Delta Lake 3.2.0. The custom Spark image downloads Delta/S3A JARs during image build. If Spark cannot find Delta or S3A classes, rebuild the image:

```bash
make build
make pipeline
```

## Trino cannot see tables

Gold tables are written by Spark as Delta folders. Register them in Trino with:

```bash
make register-trino
```

If Trino does not start, check `config/trino/etc/jvm.config`; this project includes the JVM flags required by Trino 449 on newer Java runtimes. If registration still fails, use Spark SQL for the core demo and present Trino as the serving extension.

## Superset connection problems

Superset may take a few minutes to initialize. Check:

```bash
docker compose logs superset
```

Use this SQLAlchemy URI for Trino:

```text
trino://user@trino:8080/delta/default
```

If the Trino Python driver is unavailable in the Superset image, install a custom Superset image or use exported query results for the dashboard demo.

This project includes `docker/superset/Dockerfile`, which installs Trino SQLAlchemy support for the optional full-stack demo.

## Out-of-memory issues

Use one month of data or the demo sample:

```text
CITIBIKE_MONTHS=202401
SPARK_DRIVER_MEMORY=1g
SPARK_EXECUTOR_MEMORY=1g
```

Then rerun:

```bash
make down
make up
```

## Dataset too large

Use only 1-3 months for the course demo. Full Citi Bike history is much larger and can require more disk, RAM, and time.
