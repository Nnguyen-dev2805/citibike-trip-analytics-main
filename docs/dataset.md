# Dataset: NYC Citi Bike System Data

Source: <https://citibikenyc.com/system-data>

The project uses Citi Bike trip history data. Each record represents one bike ride and includes timestamps, station information, coordinates, bike type, and user type.

## Important Columns

- `ride_id`: unique ride identifier
- `rideable_type`: classic bike, electric bike, or other bike type
- `started_at`: trip start timestamp
- `ended_at`: trip end timestamp
- `start_station_name`, `start_station_id`: origin station
- `end_station_name`, `end_station_id`: destination station
- `start_lat`, `start_lng`: origin coordinates
- `end_lat`, `end_lng`: destination coordinates
- `member_casual`: member or casual user

## Data Quality Issues

- Missing station names or IDs
- Missing coordinates
- Null `ride_id`
- Invalid timestamps
- `ended_at <= started_at`
- Extremely short or long trips
- Schema differences between old and new Citi Bike file versions

## Why This Dataset Fits Big Data / Lakehouse

Citi Bike produces large monthly files and continuous historical data. The dataset is semi-operational, time-based, and useful for multiple analytical questions. It is suitable for demonstrating raw ingestion, cleaning, partitioned storage, aggregation, SQL querying, and dashboarding.

## Demo Months

The default demo month is `202401`. For stronger analysis, use:

```text
CITIBIKE_MONTHS=202401,202402,202403
```

For a fast classroom demo without internet, run:

```bash
make sample-data
```
