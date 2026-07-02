from __future__ import annotations

import logging
import os
import re

from pyspark.sql import DataFrame, functions as F

from src.quality.data_quality_checks import quality_summary, require_non_empty
from src.utils.geo import haversine_km_col
from src.utils.paths import bronze_path, silver_path
from src.utils.spark_session import create_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("transform_silver")

COLUMN_ALIASES = {
    "rideid": "ride_id",
    "ride_id": "ride_id",
    "rideabletype": "rideable_type",
    "rideable_type": "rideable_type",
    "startedat": "started_at",
    "started_at": "started_at",
    "starttime": "started_at",
    "endedat": "ended_at",
    "ended_at": "ended_at",
    "stoptime": "ended_at",
    "startstationname": "start_station_name",
    "start_station_name": "start_station_name",
    "startstationid": "start_station_id",
    "start_station_id": "start_station_id",
    "endstationname": "end_station_name",
    "end_station_name": "end_station_name",
    "endstationid": "end_station_id",
    "end_station_id": "end_station_id",
    "startlat": "start_lat",
    "start_lat": "start_lat",
    "startlng": "start_lng",
    "start_lng": "start_lng",
    "startlon": "start_lng",
    "endlat": "end_lat",
    "end_lat": "end_lat",
    "endlng": "end_lng",
    "end_lng": "end_lng",
    "endlon": "end_lng",
    "membercasual": "member_casual",
    "member_casual": "member_casual",
    "usertype": "member_casual",
}

REQUIRED_COLUMNS = [
    "ride_id",
    "started_at",
    "ended_at",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
]


def canonical_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    compact = normalized.replace("_", "")
    return COLUMN_ALIASES.get(normalized, COLUMN_ALIASES.get(compact, normalized))


def normalize_columns(df: DataFrame) -> DataFrame:
    seen: dict[str, int] = {}
    renamed = df
    for old_name in df.columns:
        new_name = canonical_name(old_name)
        if new_name in seen:
            seen[new_name] += 1
            new_name = f"{new_name}_{seen[new_name]}"
        else:
            seen[new_name] = 0
        if old_name != new_name:
            renamed = renamed.withColumnRenamed(old_name, new_name)
    return renamed


def transform_to_silver(df: DataFrame) -> DataFrame:
    df = normalize_columns(df)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required Citi Bike columns after normalization: {missing}")

    for optional_col in ["rideable_type", "member_casual", "start_station_name", "end_station_name"]:
        if optional_col not in df.columns:
            df = df.withColumn(optional_col, F.lit(None).cast("string"))

    typed = (
        df.withColumn("started_at", F.to_timestamp("started_at"))
        .withColumn("ended_at", F.to_timestamp("ended_at"))
        .withColumn("start_lat", F.col("start_lat").cast("double"))
        .withColumn("start_lng", F.col("start_lng").cast("double"))
        .withColumn("end_lat", F.col("end_lat").cast("double"))
        .withColumn("end_lng", F.col("end_lng").cast("double"))
    )
    typed = typed.withColumn(
        "member_casual",
        F.when(F.lower(F.col("member_casual")).isin("member", "subscriber"), F.lit("member"))
        .when(F.lower(F.col("member_casual")).isin("casual", "customer"), F.lit("casual"))
        .otherwise(F.lower(F.col("member_casual"))),
    ).withColumn("rideable_type", F.lower(F.col("rideable_type")))

    cleaned = typed.filter(
        F.col("ride_id").isNotNull()
        & F.col("started_at").isNotNull()
        & F.col("ended_at").isNotNull()
        & (F.col("ended_at") > F.col("started_at"))
    )

    silver = (
        cleaned.withColumn(
            "trip_duration_minutes",
            (F.col("ended_at").cast("long") - F.col("started_at").cast("long")) / F.lit(60.0),
        )
        .filter(F.col("trip_duration_minutes") > 0)
        .withColumn("start_date", F.to_date("started_at"))
        .withColumn("start_hour", F.hour("started_at"))
        .withColumn("day_of_week", F.date_format("started_at", "EEEE"))
        .withColumn("day_of_week_num", F.dayofweek("started_at"))
        .withColumn("month", F.date_format("started_at", "yyyy-MM"))
        .withColumn("is_weekend", F.col("day_of_week_num").isin([1, 7]))
        .withColumn("distance_km", haversine_km_col("start_lat", "start_lng", "end_lat", "end_lng"))
        .withColumn("data_layer", F.lit("silver"))
    )

    selected = [
        "ride_id",
        "rideable_type",
        "started_at",
        "ended_at",
        "start_station_name",
        "start_station_id",
        "end_station_name",
        "end_station_id",
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
        "member_casual",
        "trip_duration_minutes",
        "start_date",
        "start_hour",
        "day_of_week",
        "day_of_week_num",
        "month",
        "is_weekend",
        "distance_km",
        "ingestion_timestamp",
        "source_file",
        "data_layer",
    ]
    return silver.select([col for col in selected if col in silver.columns])


def write_silver(input_path: str | None = None, output_path: str | None = None) -> None:
    spark = create_spark("citibike-transform-silver")
    input_path = input_path or os.getenv("BRONZE_PATH", bronze_path())
    output_path = output_path or os.getenv("SILVER_PATH", silver_path())

    LOGGER.info("Reading Bronze Delta table from %s", input_path)
    bronze = spark.read.format("delta").load(input_path)
    silver = transform_to_silver(bronze)
    require_non_empty(silver, "Silver Citi Bike table")

    LOGGER.info("Data quality summary after Silver cleaning")
    quality_summary(silver).show(truncate=False)

    LOGGER.info("Writing Silver Delta table to %s", output_path)
    (
        silver.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("month")
        .save(output_path)
    )
    LOGGER.info("Silver rows written: %s", silver.count())
    spark.stop()


if __name__ == "__main__":
    write_silver()
