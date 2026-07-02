from pyspark.sql import DataFrame, functions as F


def quality_summary(df: DataFrame) -> DataFrame:
    return df.agg(
        F.count("*").alias("rows"),
        F.countDistinct("ride_id").alias("distinct_ride_ids"),
        F.sum(F.when(F.col("ride_id").isNull(), 1).otherwise(0)).alias("null_ride_id"),
        F.sum(F.when(F.col("started_at").isNull(), 1).otherwise(0)).alias("null_started_at"),
        F.sum(F.when(F.col("ended_at").isNull(), 1).otherwise(0)).alias("null_ended_at"),
        F.sum(F.when(F.col("ended_at") <= F.col("started_at"), 1).otherwise(0)).alias("non_positive_time_rows"),
    )


def require_non_empty(df: DataFrame, name: str) -> None:
    if df.limit(1).count() == 0:
        raise ValueError(f"{name} is empty. Check input paths and data filters.")
