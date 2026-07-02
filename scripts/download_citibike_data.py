from __future__ import annotations

import os
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.utils.s3 import ensure_bucket, upload_file

load_dotenv()

BASE_URL = "https://s3.amazonaws.com/tripdata"
BUCKET = os.getenv("MINIO_BUCKET", "lakehouse")
MONTHS = [m.strip() for m in os.getenv("CITIBIKE_MONTHS", "202401").split(",") if m.strip()]
OUT_DIR = Path(os.getenv("CITIBIKE_DOWNLOAD_DIR", "/opt/project/data/raw"))


def candidate_urls(month: str) -> list[str]:
    return [
        f"{BASE_URL}/{month}-citibike-tripdata.csv.zip",
        f"{BASE_URL}/{month}-citibike-tripdata.zip",
        f"{BASE_URL}/{month}-citibike-tripdata.csv.gz",
    ]


def download_month(month: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in candidate_urls(month):
        local_file = OUT_DIR / url.rsplit("/", 1)[-1]
        try:
            print(f"Downloading {url}")
            response = requests.get(url, timeout=120)
            if response.status_code == 200 and response.content:
                local_file.write_bytes(response.content)
                print(f"Saved {local_file}")
                return local_file
            errors.append(f"{url}: HTTP {response.status_code}")
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError(f"Could not download Citi Bike month {month}. Tried: {errors}")


def extract_if_zip(path: Path) -> list[Path]:
    if path.suffix != ".zip":
        return [path]
    extracted: list[Path] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv"):
                target = OUT_DIR / Path(name).name
                with archive.open(name) as source, target.open("wb") as dest:
                    dest.write(source.read())
                extracted.append(target)
    if not extracted:
        raise RuntimeError(f"No CSV files found inside {path}")
    return extracted


def main() -> None:
    ensure_bucket(BUCKET)
    print(f"Using months: {', '.join(MONTHS)}")
    for month in MONTHS:
        downloaded = download_month(month)
        upload_file(str(downloaded), BUCKET, f"source-zips/citibike/{downloaded.name}")
        for csv_file in extract_if_zip(downloaded):
            upload_file(str(csv_file), BUCKET, f"raw/citibike/{csv_file.name}")
            print(f"Uploaded raw CSV to s3://{BUCKET}/raw/citibike/{csv_file.name}")


if __name__ == "__main__":
    main()
