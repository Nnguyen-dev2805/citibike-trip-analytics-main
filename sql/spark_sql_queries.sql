-- Spark SQL examples. Run after Gold tables are built.
-- In Spark notebooks, first register paths as temp views, for example:
-- CREATE OR REPLACE TEMP VIEW gold_daily_rides USING DELTA OPTIONS (path 's3a://lakehouse/gold/citibike/gold_daily_rides');

-- 1. Which days have the highest number of rides?
SELECT ride_date, total_rides, member_rides, casual_rides, avg_duration_minutes, avg_distance_km
FROM gold_daily_rides
ORDER BY total_rides DESC
LIMIT 10;

-- 2. Which hours have the highest demand?
SELECT day_of_week, start_hour, total_rides, avg_duration_minutes
FROM gold_hourly_demand
ORDER BY total_rides DESC
LIMIT 10;

-- 3. Most popular starting stations
SELECT start_station_name, total_starts, avg_duration_minutes
FROM gold_top_start_stations
ORDER BY total_starts DESC
LIMIT 20;

-- 4. Most popular ending stations
SELECT end_station_name, total_ends, avg_duration_minutes
FROM gold_top_end_stations
ORDER BY total_ends DESC
LIMIT 20;

-- 5. Member vs casual behavior
SELECT member_casual, total_rides, avg_duration_minutes, avg_distance_km, weekend_rides, weekday_rides
FROM gold_user_type_behavior
ORDER BY total_rides DESC;

-- 6. Bike type usage
SELECT rideable_type, total_rides, avg_duration_minutes, avg_distance_km
FROM gold_bike_type_usage
ORDER BY total_rides DESC;

-- 7. Common origin-destination pairs
SELECT start_station_name, end_station_name, total_rides, avg_duration_minutes
FROM gold_station_od_pairs
ORDER BY total_rides DESC
LIMIT 20;
