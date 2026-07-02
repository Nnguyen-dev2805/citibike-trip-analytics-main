-- Trino examples for the Delta catalog.
-- Recommended: run `make register-trino` first. The calls below show the SQL equivalent.
-- If a table is already registered, skip its register_table call.

CREATE SCHEMA IF NOT EXISTS delta.default;

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_daily_rides',
  table_location => 's3://lakehouse/gold/citibike/gold_daily_rides'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_hourly_demand',
  table_location => 's3://lakehouse/gold/citibike/gold_hourly_demand'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_top_start_stations',
  table_location => 's3://lakehouse/gold/citibike/gold_top_start_stations'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_top_end_stations',
  table_location => 's3://lakehouse/gold/citibike/gold_top_end_stations'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_user_type_behavior',
  table_location => 's3://lakehouse/gold/citibike/gold_user_type_behavior'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_bike_type_usage',
  table_location => 's3://lakehouse/gold/citibike/gold_bike_type_usage'
);

CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'gold_station_od_pairs',
  table_location => 's3://lakehouse/gold/citibike/gold_station_od_pairs'
);

SELECT ride_date, total_rides, member_rides, casual_rides
FROM delta.default.gold_daily_rides
ORDER BY total_rides DESC
LIMIT 10;

SELECT day_of_week, start_hour, total_rides
FROM delta.default.gold_hourly_demand
ORDER BY total_rides DESC
LIMIT 10;

SELECT start_station_name, total_starts
FROM delta.default.gold_top_start_stations
ORDER BY total_starts DESC
LIMIT 20;
