import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from src.utils.s3 import ensure_bucket, upload_file

load_dotenv()

BUCKET = os.getenv("MINIO_BUCKET", "lakehouse")
OUT_DIR = Path(os.getenv("CITIBIKE_DOWNLOAD_DIR", "/opt/project/data/raw"))
DEMO_FILE = OUT_DIR / "202401-citibike-demo.csv"

ROWS = [
    {
        "ride_id": "demo-001",
        "rideable_type": "classic_bike",
        "started_at": "2024-01-01 08:10:00",
        "ended_at": "2024-01-01 08:24:00",
        "start_station_name": "Broadway & W 58 St",
        "start_station_id": "6948.10",
        "end_station_name": "W 41 St & 8 Ave",
        "end_station_id": "6602.03",
        "start_lat": "40.766953",
        "start_lng": "-73.981693",
        "end_lat": "40.756405",
        "end_lng": "-73.990026",
        "member_casual": "member",
    },
    {
        "ride_id": "demo-002",
        "rideable_type": "electric_bike",
        "started_at": "2024-01-06 14:00:00",
        "ended_at": "2024-01-06 14:31:30",
        "start_station_name": "E 17 St & Broadway",
        "start_station_id": "5980.07",
        "end_station_name": "Pier 40 - Hudson River Park",
        "end_station_id": "5696.03",
        "start_lat": "40.737050",
        "start_lng": "-73.990093",
        "end_lat": "40.727714",
        "end_lng": "-74.011296",
        "member_casual": "casual",
    },
    {
        "ride_id": "demo-003",
        "rideable_type": "classic_bike",
        "started_at": "2024-01-07 18:15:00",
        "ended_at": "2024-01-07 18:22:00",
        "start_station_name": "W 41 St & 8 Ave",
        "start_station_id": "6602.03",
        "end_station_name": "Broadway & W 58 St",
        "end_station_id": "6948.10",
        "start_lat": "40.756405",
        "start_lng": "-73.990026",
        "end_lat": "40.766953",
        "end_lng": "-73.981693",
        "member_casual": "member",
    },
    {
        "ride_id": "demo-004",
        "rideable_type": "electric_bike",
        "started_at": "2024-01-08 09:05:00",
        "ended_at": "2024-01-08 09:48:00",
        "start_station_name": "Pier 40 - Hudson River Park",
        "start_station_id": "5696.03",
        "end_station_name": "E 17 St & Broadway",
        "end_station_id": "5980.07",
        "start_lat": "40.727714",
        "start_lng": "-74.011296",
        "end_lat": "40.737050",
        "end_lng": "-73.990093",
        "member_casual": "casual",
    },
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with DEMO_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(ROWS)

    ensure_bucket(BUCKET)
    upload_file(str(DEMO_FILE), BUCKET, f"raw/citibike/{DEMO_FILE.name}")
    print(f"Uploaded demo data to s3://{BUCKET}/raw/citibike/{DEMO_FILE.name}")


if __name__ == "__main__":
    main()
