import os


def bucket() -> str:
    return os.getenv("MINIO_BUCKET", "lakehouse")


def s3a_root() -> str:
    return f"s3a://{bucket()}"


def s3_root() -> str:
    return f"s3://{bucket()}"


def raw_path() -> str:
    return f"{s3a_root()}/raw/citibike"


def bronze_path() -> str:
    return f"{s3a_root()}/bronze/citibike"


def silver_path() -> str:
    return f"{s3a_root()}/silver/citibike"


def gold_root() -> str:
    return f"{s3a_root()}/gold/citibike"


def gold_table_path(table_name: str) -> str:
    return f"{gold_root()}/{table_name}"
