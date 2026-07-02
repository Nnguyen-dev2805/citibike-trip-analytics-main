import os
from pathlib import Path

import boto3
from botocore.client import Config


def minio_client():
    endpoint = (
        os.getenv("MINIO_CLIENT_ENDPOINT")
        or os.getenv("MINIO_ENDPOINT")
        or os.getenv("MINIO_PUBLIC_ENDPOINT")
        or "http://localhost:9000"
    )
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", os.getenv("MINIO_ROOT_USER", "minioadmin")),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(bucket_name: str) -> None:
    client = minio_client()
    existing = [bucket["Name"] for bucket in client.list_buckets().get("Buckets", [])]
    if bucket_name not in existing:
        client.create_bucket(Bucket=bucket_name)


def upload_file(local_path: str, bucket_name: str, key: str) -> None:
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot upload missing file: {path}")
    minio_client().upload_file(str(path), bucket_name, key)
