import math


EARTH_RADIUS_KM = 6371.0088


def haversine_km_python(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> float:
    """Pure Python Haversine distance, useful for tests."""
    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lng)
    lat2 = math.radians(end_lat)
    lon2 = math.radians(end_lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def haversine_km_col(start_lat: str, start_lng: str, end_lat: str, end_lng: str):
    """Spark Column expression for Haversine distance in kilometers."""
    from pyspark.sql import functions as F

    lat1 = F.radians(F.col(start_lat).cast("double"))
    lon1 = F.radians(F.col(start_lng).cast("double"))
    lat2 = F.radians(F.col(end_lat).cast("double"))
    lon2 = F.radians(F.col(end_lng).cast("double"))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = F.pow(F.sin(dlat / 2), 2) + F.cos(lat1) * F.cos(lat2) * F.pow(F.sin(dlon / 2), 2)
    return 2 * F.lit(EARTH_RADIUS_KM) * F.asin(F.sqrt(a))
