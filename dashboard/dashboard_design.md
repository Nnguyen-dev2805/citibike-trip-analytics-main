# Dashboard Design

## Dashboard Title

NYC Citi Bike Lakehouse Analytics

## Recommended Charts

1. Daily ride volume
   - Dataset: `gold_daily_rides`
   - Chart: line chart
   - X-axis: `ride_date`
   - Y-axis: `total_rides`

2. Hourly demand heatmap
   - Dataset: `gold_hourly_demand`
   - Chart: heatmap or pivot table
   - Rows: `day_of_week`
   - Columns: `start_hour`
   - Metric: `total_rides`

3. Top start stations
   - Dataset: `gold_top_start_stations`
   - Chart: horizontal bar
   - Dimension: `start_station_name`
   - Metric: `total_starts`

4. Top end stations
   - Dataset: `gold_top_end_stations`
   - Chart: horizontal bar
   - Dimension: `end_station_name`
   - Metric: `total_ends`

5. Member vs casual behavior
   - Dataset: `gold_user_type_behavior`
   - Chart: grouped bar or table
   - Metrics: `total_rides`, `avg_duration_minutes`, `avg_distance_km`

6. Bike type usage
   - Dataset: `gold_bike_type_usage`
   - Chart: bar chart
   - Dimension: `rideable_type`
   - Metric: `total_rides`

7. Origin-destination pairs
   - Dataset: `gold_station_od_pairs`
   - Chart: table
   - Columns: `start_station_name`, `end_station_name`, `total_rides`, `avg_duration_minutes`

## Dashboard Filters

- Date range
- Member/casual user type
- Bike type
- Station name

## Interpretation Notes

- Members often show commute-like usage patterns.
- Casual users may have longer durations and stronger weekend patterns.
- Hourly demand helps identify commute peaks or tourism/recreation periods.
- Top station tables help identify high-traffic locations.
