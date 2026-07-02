import os
from src.utils.spark_session import create_spark
from src.utils.paths import silver_path

def main():
    spark = create_spark("export-clean-data")
    print("Reading silver delta table...")
    df = spark.read.format("delta").load(silver_path())
    
    output_dir = "/opt/project/dataclean"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "citibike_nyc_cleaned.parquet")
    
    print(f"Exporting silver delta table to local parquet: {output_file}")
    df.write.mode("overwrite").parquet(output_file)
    print("Export completed successfully!")
    spark.stop()

if __name__ == "__main__":
    main()
