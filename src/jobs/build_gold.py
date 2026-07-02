from __future__ import annotations

import logging
import os

from pyspark.sql import DataFrame, functions as F

from src.quality.data_quality_checks import require_non_empty
from src.utils.paths import gold_table_path, silver_path
from src.utils.spark_session import create_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("build_gold")


def write_delta(df: DataFrame, table_name: str, partition_cols: list[str] | None = None) -> None:
    output_path = gold_table_path(table_name)
    writer = df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    LOGGER.info("Writing %s to %s", table_name, output_path)
    writer.save(output_path)


def build_gold_tables(silver: DataFrame) -> dict[str, DataFrame]:
    member_rides = F.sum(F.when(F.col("member_casual") == "member", 1).otherwise(0)).cast("long")
    casual_rides = F.sum(F.when(F.col("member_casual") == "casual", 1).otherwise(0)).cast("long")

    return {
        "gold_daily_rides": (
            silver.groupBy(F.col("start_date").alias("ride_date"))
            .agg(
                F.count("*").alias("total_rides"),
                member_rides.alias("member_rides"),
                casual_rides.alias("casual_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
                F.round(F.avg("distance_km"), 3).alias("avg_distance_km"),
            )
            .orderBy("ride_date")
        ),
        "gold_hourly_demand": (
            silver.groupBy("day_of_week", "day_of_week_num", "start_hour")
            .agg(
                F.count("*").alias("total_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
            )
            .orderBy("day_of_week_num", "start_hour")
            .select("day_of_week", "start_hour", "total_rides", "avg_duration_minutes")
        ),
        "gold_top_start_stations": (
            silver.filter(F.col("start_station_name").isNotNull())
            .groupBy("start_station_name")
            .agg(
                F.count("*").alias("total_starts"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
            )
            .orderBy(F.desc("total_starts"))
        ),
        "gold_top_end_stations": (
            silver.filter(F.col("end_station_name").isNotNull())
            .groupBy("end_station_name")
            .agg(
                F.count("*").alias("total_ends"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
            )
            .orderBy(F.desc("total_ends"))
        ),
        "gold_user_type_behavior": (
            silver.groupBy("member_casual")
            .agg(
                F.count("*").alias("total_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
                F.round(F.avg("distance_km"), 3).alias("avg_distance_km"),
                F.sum(F.when(F.col("is_weekend"), 1).otherwise(0)).cast("long").alias("weekend_rides"),
                F.sum(F.when(~F.col("is_weekend"), 1).otherwise(0)).cast("long").alias("weekday_rides"),
            )
            .orderBy(F.desc("total_rides"))
        ),
        "gold_bike_type_usage": (
            silver.groupBy("rideable_type")
            .agg(
                F.count("*").alias("total_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
                F.round(F.avg("distance_km"), 3).alias("avg_distance_km"),
            )
            .orderBy(F.desc("total_rides"))
        ),
        "gold_station_od_pairs": (
            silver.filter(F.col("start_station_name").isNotNull() & F.col("end_station_name").isNotNull())
            .groupBy("start_station_name", "end_station_name")
            .agg(
                F.count("*").alias("total_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
            )
            .orderBy(F.desc("total_rides"))
        ),
        "gold_monthly_summary": (
            silver.groupBy("month")
            .agg(
                F.count("*").alias("total_rides"),
                member_rides.alias("member_rides"),
                casual_rides.alias("casual_rides"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
                F.round(F.avg("distance_km"), 3).alias("avg_distance_km"),
                F.count_distinct("start_station_name").alias("unique_start_stations"),
                F.count_distinct("end_station_name").alias("unique_end_stations"),
            )
            .orderBy("month")
        ),
    }


def build_gold(input_path: str | None = None) -> None:
    spark = create_spark("citibike-build-gold")
    input_path = input_path or os.getenv("SILVER_PATH", silver_path())
    LOGGER.info("Reading Silver Delta table from %s", input_path)
    silver = spark.read.format("delta").load(input_path)
    require_non_empty(silver, "Silver Citi Bike table")

    tables = build_gold_tables(silver)
    for name, df in tables.items():
        require_non_empty(df, name)
        partition_cols = ["ride_date"] if name == "gold_daily_rides" else None
        write_delta(df, name, partition_cols)
        LOGGER.info("%s rows: %s", name, df.count())
    spark.stop()


if __name__ == "__main__":
    build_gold()
