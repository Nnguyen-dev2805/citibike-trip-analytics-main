from src.utils.geo import haversine_km_python


def test_haversine_midtown_to_times_square_area():
    distance = haversine_km_python(40.766953, -73.981693, 40.756405, -73.990026)
    assert 1.2 < distance < 1.5
