from __future__ import annotations

import logging
import os

from pyspark.sql import functions as F

from src.quality.data_quality_checks import require_non_empty
from src.utils.paths import bronze_path, raw_path
from src.utils.spark_session import create_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("ingest_bronze")


def ingest_bronze(input_path: str | None = None, output_path: str | None = None) -> None:
    spark = create_spark("citibike-ingest-bronze")
    input_path = input_path or os.getenv("RAW_INPUT_PATH", raw_path())
    output_path = output_path or os.getenv("BRONZE_PATH", bronze_path())

    LOGGER.info("Reading raw Citi Bike CSV files from %s", input_path)
    df = (
        spark.read.option("header", "true")
        .option("inferSchema", "false")
        .option("multiLine", "false")
        .csv(input_path)
    )
    require_non_empty(df, "raw Citi Bike input")

    bronze = (
        df.withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
        .withColumn("data_layer", F.lit("bronze"))
    )

    LOGGER.info("Writing Bronze Delta table to %s", output_path)
    (
        bronze.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(output_path)
    )
    LOGGER.info("Bronze rows written: %s", bronze.count())
    spark.stop()


if __name__ == "__main__":
    ingest_bronze()
