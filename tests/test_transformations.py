import pytest

pytest.importorskip("pyspark")

from pyspark.sql import SparkSession

from src.jobs.transform_silver import canonical_name, transform_to_silver


def test_canonical_name_handles_citibike_columns():
    assert canonical_name("started_at") == "started_at"
    assert canonical_name("Start Station Name") == "start_station_name"
    assert canonical_name("end_lng") == "end_lng"


def test_transform_to_silver_filters_invalid_rows():
    spark = SparkSession.builder.master("local[1]").appName("test-silver").getOrCreate()
    rows = [
        {
            "ride_id": "ok",
            "rideable_type": "classic_bike",
            "started_at": "2024-01-01 10:00:00",
            "ended_at": "2024-01-01 10:10:00",
            "start_station_name": "A",
            "end_station_name": "B",
            "start_lat": "40.0",
            "start_lng": "-73.0",
            "end_lat": "40.1",
            "end_lng": "-73.1",
            "member_casual": "member",
        },
        {
            "ride_id": None,
            "rideable_type": "classic_bike",
            "started_at": "2024-01-01 10:00:00",
            "ended_at": "2024-01-01 10:10:00",
            "start_station_name": "A",
            "end_station_name": "B",
            "start_lat": "40.0",
            "start_lng": "-73.0",
            "end_lat": "40.1",
            "end_lng": "-73.1",
            "member_casual": "member",
        },
    ]
    silver = transform_to_silver(spark.createDataFrame(rows))
    assert silver.count() == 1
    assert silver.select("trip_duration_minutes").first()[0] == 10.0
    spark.stop()


def test_transform_to_silver_normalizes_legacy_user_type_values():
    spark = SparkSession.builder.master("local[1]").appName("test-legacy-user-type").getOrCreate()
    rows = [
        {
            "ride_id": "legacy",
            "rideable_type": "Classic_Bike",
            "started_at": "2024-01-01 10:00:00",
            "ended_at": "2024-01-01 10:10:00",
            "start_station_name": "A",
            "end_station_name": "B",
            "start_lat": "40.0",
            "start_lng": "-73.0",
            "end_lat": "40.1",
            "end_lng": "-73.1",
            "usertype": "Subscriber",
        }
    ]
    silver = transform_to_silver(spark.createDataFrame(rows))
    row = silver.select("member_casual", "rideable_type").first()
    assert row["member_casual"] == "member"
    assert row["rideable_type"] == "classic_bike"
    spark.stop()
