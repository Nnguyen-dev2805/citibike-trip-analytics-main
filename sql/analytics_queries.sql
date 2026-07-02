-- Analytics questions mapped to Gold tables.

-- Highest ride days: gold_daily_rides
SELECT * FROM gold_daily_rides ORDER BY total_rides DESC LIMIT 10;

-- Peak demand hours: gold_hourly_demand
SELECT * FROM gold_hourly_demand ORDER BY total_rides DESC LIMIT 10;

-- Top start stations: gold_top_start_stations
SELECT * FROM gold_top_start_stations ORDER BY total_starts DESC LIMIT 20;

-- Top end stations: gold_top_end_stations
SELECT * FROM gold_top_end_stations ORDER BY total_ends DESC LIMIT 20;

-- User type comparison: gold_user_type_behavior
SELECT
  member_casual,
  total_rides,
  avg_duration_minutes,
  avg_distance_km,
  weekend_rides,
  weekday_rides,
  ROUND(weekend_rides * 100.0 / NULLIF(total_rides, 0), 2) AS weekend_share_pct
FROM gold_user_type_behavior;

-- Bike type usage: gold_bike_type_usage
SELECT * FROM gold_bike_type_usage ORDER BY total_rides DESC;

-- OD pairs: gold_station_od_pairs
SELECT * FROM gold_station_od_pairs ORDER BY total_rides DESC LIMIT 20;
