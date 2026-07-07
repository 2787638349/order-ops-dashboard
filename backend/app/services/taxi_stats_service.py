import time
from datetime import datetime, time as datetime_time, timedelta

from sqlalchemy import text

from app.extensions import db
from app.models.taxi_stats import TaxiStatsMeta


PAYMENT_CASE_SQL = """
CASE COALESCE(payment_type, 0)
    WHEN 1 THEN '信用卡'
    WHEN 2 THEN '现金'
    WHEN 3 THEN '免费'
    WHEN 4 THEN '争议'
    WHEN 5 THEN '未知'
    WHEN 6 THEN '作废'
    ELSE '未知'
END
"""

AGGREGATE_TABLES = [
    "taxi_daily_stats",
    "taxi_hourly_stats",
    "taxi_payment_stats",
    "taxi_passenger_stats",
    "taxi_distance_stats",
    "taxi_pickup_location_stats",
    "taxi_dropoff_location_stats",
]


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_filter_sql(alias="taxi_trips"):
    return f"""
        (:start_datetime IS NULL OR {alias}.pickup_time >= :start_datetime)
        AND (:end_datetime IS NULL OR {alias}.pickup_time < :end_datetime)
    """


def stat_date_filter_sql(column="stat_date"):
    return f"""
        (:start_date IS NULL OR {column} >= :start_date)
        AND (:end_date IS NULL OR {column} <= :end_date)
    """


def _upsert_meta(status, message):
    meta = TaxiStatsMeta.query.filter_by(stats_name="taxi_analysis").first()
    if meta is None:
        meta = TaxiStatsMeta(stats_name="taxi_analysis")
        db.session.add(meta)
    meta.status = status
    meta.message = (message or "")[:450]
    meta.last_rebuild_time = datetime.now()


def _delete_existing_stats(params):
    for table_name in AGGREGATE_TABLES:
        db.session.execute(
            text(f"DELETE FROM {table_name} WHERE {stat_date_filter_sql()}"),
            params,
        )


def _insert_daily_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_daily_stats (
            stat_date,
            total_trips,
            normal_trips,
            abnormal_trips,
            total_amount,
            fare_amount,
            tip_amount,
            total_distance,
            total_duration,
            avg_amount,
            avg_distance,
            avg_duration,
            tip_rate,
            created_at,
            updated_at
        )
        SELECT
            DATE(pickup_time) AS stat_date,
            COUNT(*) AS total_trips,
            SUM(CASE WHEN is_abnormal = 0 THEN 1 ELSE 0 END) AS normal_trips,
            SUM(CASE WHEN is_abnormal = 1 THEN 1 ELSE 0 END) AS abnormal_trips,
            SUM(CASE WHEN total_amount >= 0 THEN total_amount ELSE 0 END) AS total_amount,
            SUM(CASE WHEN fare_amount >= 0 THEN fare_amount ELSE 0 END) AS fare_amount,
            SUM(CASE WHEN tip_amount >= 0 THEN tip_amount ELSE 0 END) AS tip_amount,
            SUM(CASE WHEN is_abnormal = 0 AND trip_distance > 0 THEN trip_distance ELSE 0 END) AS total_distance,
            SUM(CASE WHEN is_abnormal = 0 AND trip_duration_min > 0 THEN trip_duration_min ELSE 0 END) AS total_duration,
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE SUM(CASE WHEN total_amount >= 0 THEN total_amount ELSE 0 END) / COUNT(*)
            END AS avg_amount,
            CASE
                WHEN SUM(CASE WHEN is_abnormal = 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN is_abnormal = 0 AND trip_distance > 0 THEN trip_distance ELSE 0 END)
                     / SUM(CASE WHEN is_abnormal = 0 THEN 1 ELSE 0 END)
            END AS avg_distance,
            CASE
                WHEN SUM(CASE WHEN is_abnormal = 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN is_abnormal = 0 AND trip_duration_min > 0 THEN trip_duration_min ELSE 0 END)
                     / SUM(CASE WHEN is_abnormal = 0 THEN 1 ELSE 0 END)
            END AS avg_duration,
            CASE
                WHEN SUM(CASE WHEN fare_amount >= 0 THEN fare_amount ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN tip_amount >= 0 THEN tip_amount ELSE 0 END)
                     / SUM(CASE WHEN fare_amount >= 0 THEN fare_amount ELSE 0 END) * 100
            END AS tip_rate,
            NOW(),
            NOW()
        FROM taxi_trips
        WHERE {date_filter}
        GROUP BY DATE(pickup_time)
        """),
        params,
    )


def _insert_hourly_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_hourly_stats (stat_date, hour, trip_count, created_at, updated_at)
        SELECT DATE(pickup_time), HOUR(pickup_time), COUNT(*), NOW(), NOW()
        FROM taxi_trips
        WHERE {date_filter}
        GROUP BY DATE(pickup_time), HOUR(pickup_time)
        """),
        params,
    )


def _insert_payment_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_payment_stats (stat_date, payment_type, payment_name, trip_count, created_at, updated_at)
        SELECT
            DATE(pickup_time),
            COALESCE(payment_type, 0),
            {PAYMENT_CASE_SQL},
            COUNT(*),
            NOW(),
            NOW()
        FROM taxi_trips
        WHERE {date_filter}
        GROUP BY DATE(pickup_time), COALESCE(payment_type, 0), {PAYMENT_CASE_SQL}
        """),
        params,
    )


def _insert_passenger_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_passenger_stats (stat_date, passenger_count, trip_count, created_at, updated_at)
        SELECT DATE(pickup_time), passenger_count, COUNT(*), NOW(), NOW()
        FROM taxi_trips
        WHERE {date_filter}
          AND passenger_count IS NOT NULL
        GROUP BY DATE(pickup_time), passenger_count
        """),
        params,
    )


def _insert_distance_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_distance_stats (stat_date, distance_range, range_order, trip_count, created_at, updated_at)
        SELECT
            stat_date,
            distance_range,
            range_order,
            COUNT(*),
            NOW(),
            NOW()
        FROM (
            SELECT
                DATE(pickup_time) AS stat_date,
                CASE
                    WHEN trip_distance > 0 AND trip_distance <= 1 THEN '0-1'
                    WHEN trip_distance > 1 AND trip_distance <= 3 THEN '1-3'
                    WHEN trip_distance > 3 AND trip_distance <= 5 THEN '3-5'
                    WHEN trip_distance > 5 AND trip_distance <= 10 THEN '5-10'
                    WHEN trip_distance > 10 AND trip_distance <= 20 THEN '10-20'
                    WHEN trip_distance > 20 THEN '20+'
                END AS distance_range,
                CASE
                    WHEN trip_distance > 0 AND trip_distance <= 1 THEN 1
                    WHEN trip_distance > 1 AND trip_distance <= 3 THEN 2
                    WHEN trip_distance > 3 AND trip_distance <= 5 THEN 3
                    WHEN trip_distance > 5 AND trip_distance <= 10 THEN 4
                    WHEN trip_distance > 10 AND trip_distance <= 20 THEN 5
                    WHEN trip_distance > 20 THEN 6
                END AS range_order
            FROM taxi_trips
            WHERE {date_filter}
              AND is_abnormal = 0
              AND trip_distance > 0
        ) distance_rows
        WHERE distance_range IS NOT NULL
        GROUP BY stat_date, distance_range, range_order
        """),
        params,
    )


def _insert_pickup_location_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_pickup_location_stats (
            stat_date,
            pickup_location_id,
            pickup_location_name,
            pickup_borough,
            trip_count,
            created_at,
            updated_at
        )
        SELECT
            DATE(taxi_trips.pickup_time),
            taxi_trips.pickup_location_id,
            CASE
                WHEN taxi_zones.borough IS NOT NULL AND taxi_zones.zone IS NOT NULL
                    THEN CONCAT(taxi_zones.borough, ' - ', taxi_zones.zone)
                WHEN taxi_zones.zone IS NOT NULL THEN taxi_zones.zone
                ELSE CAST(taxi_trips.pickup_location_id AS CHAR)
            END,
            taxi_zones.borough,
            COUNT(*),
            NOW(),
            NOW()
        FROM taxi_trips
        LEFT JOIN taxi_zones ON taxi_trips.pickup_location_id = taxi_zones.location_id
        WHERE {date_filter}
        GROUP BY DATE(taxi_trips.pickup_time), taxi_trips.pickup_location_id, taxi_zones.borough, taxi_zones.zone
        """),
        params,
    )


def _insert_dropoff_location_stats(date_filter, params):
    db.session.execute(
        text(f"""
        INSERT INTO taxi_dropoff_location_stats (
            stat_date,
            dropoff_location_id,
            dropoff_location_name,
            dropoff_borough,
            trip_count,
            created_at,
            updated_at
        )
        SELECT
            DATE(taxi_trips.pickup_time),
            taxi_trips.dropoff_location_id,
            CASE
                WHEN taxi_zones.borough IS NOT NULL AND taxi_zones.zone IS NOT NULL
                    THEN CONCAT(taxi_zones.borough, ' - ', taxi_zones.zone)
                WHEN taxi_zones.zone IS NOT NULL THEN taxi_zones.zone
                ELSE CAST(taxi_trips.dropoff_location_id AS CHAR)
            END,
            taxi_zones.borough,
            COUNT(*),
            NOW(),
            NOW()
        FROM taxi_trips
        LEFT JOIN taxi_zones ON taxi_trips.dropoff_location_id = taxi_zones.location_id
        WHERE {date_filter}
        GROUP BY DATE(taxi_trips.pickup_time), taxi_trips.dropoff_location_id, taxi_zones.borough, taxi_zones.zone
        """),
        params,
    )


def rebuild_taxi_stats(start_date=None, end_date=None):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "start_datetime": datetime.combine(start_date, datetime_time.min) if start_date else None,
        "end_datetime": datetime.combine(end_date + timedelta(days=1), datetime_time.min) if end_date else None,
    }

    started_at = time.time()
    date_filter = date_filter_sql("taxi_trips")
    range_message = f"from {start_date or 'beginning'} to {end_date or 'latest'}"

    try:
        _upsert_meta("running", f"Rebuilding taxi stats {range_message}")
        db.session.commit()

        _delete_existing_stats(params)
        _insert_daily_stats(date_filter, params)
        _insert_hourly_stats(date_filter, params)
        _insert_payment_stats(date_filter, params)
        _insert_passenger_stats(date_filter, params)
        _insert_distance_stats(date_filter, params)
        _insert_pickup_location_stats(date_filter, params)
        _insert_dropoff_location_stats(date_filter, params)

        elapsed = time.time() - started_at
        message = f"Taxi stats rebuild completed in {elapsed:.2f}s"
        _upsert_meta("completed", message)
        db.session.commit()

        return {
            "status": "completed",
            "message": message,
            "elapsedSeconds": round(elapsed, 2),
        }
    except Exception as exc:
        db.session.rollback()
        _upsert_meta("failed", str(exc))
        db.session.commit()
        raise
