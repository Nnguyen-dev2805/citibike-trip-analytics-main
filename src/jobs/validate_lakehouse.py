from __future__ import annotations

from dataclasses import dataclass

from pyspark.sql import DataFrame

from src.utils.paths import bronze_path, gold_table_path, silver_path
from src.utils.spark_session import create_spark


@dataclass(frozen=True)
class TableExpectation:
    name: str
    path: str
    required_columns: tuple[str, ...]


EXPECTATIONS = [
    TableExpectation(
        "bronze_citibike",
        bronze_path(),
        ("ride_id", "started_at", "ended_at", "ingestion_timestamp", "source_file", "data_layer"),
    ),
    TableExpectation(
        "silver_citibike",
        silver_path(),
        ("ride_id", "started_at", "ended_at", "trip_duration_minutes", "start_date", "distance_km", "data_layer"),
    ),
    TableExpectation(
        "gold_daily_rides",
        gold_table_path("gold_daily_rides"),
        ("ride_date", "total_rides", "member_rides", "casual_rides", "avg_duration_minutes", "avg_distance_km"),
    ),
    TableExpectation(
        "gold_hourly_demand",
        gold_table_path("gold_hourly_demand"),
        ("day_of_week", "start_hour", "total_rides", "avg_duration_minutes"),
    ),
    TableExpectation(
        "gold_top_start_stations",
        gold_table_path("gold_top_start_stations"),
        ("start_station_name", "total_starts", "avg_duration_minutes"),
    ),
    TableExpectation(
        "gold_top_end_stations",
        gold_table_path("gold_top_end_stations"),
        ("end_station_name", "total_ends", "avg_duration_minutes"),
    ),
    TableExpectation(
        "gold_user_type_behavior",
        gold_table_path("gold_user_type_behavior"),
        ("member_casual", "total_rides", "avg_duration_minutes", "avg_distance_km", "weekend_rides", "weekday_rides"),
    ),
    TableExpectation(
        "gold_bike_type_usage",
        gold_table_path("gold_bike_type_usage"),
        ("rideable_type", "total_rides", "avg_duration_minutes", "avg_distance_km"),
    ),
    TableExpectation(
        "gold_station_od_pairs",
        gold_table_path("gold_station_od_pairs"),
        ("start_station_name", "end_station_name", "total_rides", "avg_duration_minutes"),
    ),
    TableExpectation(
        "gold_monthly_summary",
        gold_table_path("gold_monthly_summary"),
        ("month", "total_rides", "member_rides", "casual_rides", "avg_duration_minutes", "avg_distance_km", "unique_start_stations", "unique_end_stations"),
    ),
]


def validate_columns(df: DataFrame, expectation: TableExpectation) -> None:
    missing = [column for column in expectation.required_columns if column not in df.columns]
    if missing:
        raise AssertionError(f"{expectation.name} is missing required columns: {missing}")


def main() -> None:
    spark = create_spark("citibike-validate-lakehouse")
    print("Validating Lakehouse Delta tables")
    for expectation in EXPECTATIONS:
        df = spark.read.format("delta").load(expectation.path)
        validate_columns(df, expectation)
        row_count = df.count()
        if row_count == 0:
            raise AssertionError(f"{expectation.name} is empty")
        print(f"OK {expectation.name}: {row_count} rows at {expectation.path}")
    spark.stop()


if __name__ == "__main__":
    main()
