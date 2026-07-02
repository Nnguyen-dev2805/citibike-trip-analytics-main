from src.utils.paths import gold_table_path
from src.utils.spark_session import create_spark


TABLES = [
    "gold_daily_rides",
    "gold_hourly_demand",
    "gold_top_start_stations",
    "gold_top_end_stations",
    "gold_user_type_behavior",
    "gold_bike_type_usage",
    "gold_station_od_pairs",
]


def main() -> None:
    spark = create_spark("citibike-query-gold")
    for table in TABLES:
        df = spark.read.format("delta").load(gold_table_path(table))
        print(f"\n===== {table} =====")
        df.show(20, truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()
