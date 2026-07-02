# Setup Guide

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2
- At least 8 GB RAM recommended
- Internet connection for first image/package download

## Step 1: Configure Environment

```bash
cp .env.example .env
```

Optional: edit `.env` to change months:

```text
CITIBIKE_MONTHS=202401,202402,202403
```

## Step 2: Start Services

```bash
make up
```

This starts the core demo services: MinIO, Spark master/worker, and Jupyter. The Spark image includes the Delta Lake and S3A JARs needed for MinIO access.

To start the optional analytics and BI services too:

```bash
make up-full
```

This adds Trino, Superset, and Superset PostgreSQL metadata storage.

After Gold tables are built, register them in Trino:

```bash
make register-trino
```

## Step 3: Initialize Object Storage

```bash
make init
```

This creates the `lakehouse` bucket and prefixes for raw, Bronze, Silver, Gold, and Trino metadata.

## Step 4: Load Data

Fast demo:

```bash
make sample-data
```

Official data:

```bash
make download-data
```

## Step 5: Run Pipeline

```bash
make pipeline
make validate
```

Or step by step:

```bash
make bronze
make silver
make gold
make query
make validate
```

## Step 6: Explore Services

- MinIO Console: <http://localhost:9001>
- Spark UI: <http://localhost:8080>
- JupyterLab: <http://localhost:8888>
- Trino: <http://localhost:8085> after `make up-full`
- Superset: <http://localhost:8088> after `make up-full`

## Step 7: Stop Services

```bash
make down
```

To remove all Docker volumes:

```bash
make clean
```
