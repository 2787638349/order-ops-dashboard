from datetime import datetime

from app.extensions import db


class TaxiDailyStats(db.Model):
    __tablename__ = "taxi_daily_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    total_trips = db.Column(db.Integer, nullable=False, default=0)
    normal_trips = db.Column(db.Integer, nullable=False, default=0)
    abnormal_trips = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    fare_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tip_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_distance = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_duration = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    avg_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    avg_distance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    avg_duration = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tip_rate = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", name="uk_taxi_daily_stats_date"),
        db.Index("idx_taxi_daily_stats_date", "stat_date"),
    )


class TaxiHourlyStats(db.Model):
    __tablename__ = "taxi_hourly_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "hour", name="uk_taxi_hourly_stats_date_hour"),
        db.Index("idx_taxi_hourly_stats_date", "stat_date"),
    )


class TaxiPaymentStats(db.Model):
    __tablename__ = "taxi_payment_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.Integer, nullable=False, default=0)
    payment_name = db.Column(db.String(40), nullable=False, default="Unknown")
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "payment_type", name="uk_taxi_payment_stats_date_type"),
        db.Index("idx_taxi_payment_stats_date", "stat_date"),
    )


class TaxiPassengerStats(db.Model):
    __tablename__ = "taxi_passenger_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    passenger_count = db.Column(db.Integer, nullable=False)
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "passenger_count", name="uk_taxi_passenger_stats_date_count"),
        db.Index("idx_taxi_passenger_stats_date", "stat_date"),
    )


class TaxiDistanceStats(db.Model):
    __tablename__ = "taxi_distance_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    distance_range = db.Column(db.String(20), nullable=False)
    range_order = db.Column(db.Integer, nullable=False)
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "distance_range", name="uk_taxi_distance_stats_date_range"),
        db.Index("idx_taxi_distance_stats_date_order", "stat_date", "range_order"),
    )


class TaxiPickupLocationStats(db.Model):
    __tablename__ = "taxi_pickup_location_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    pickup_location_id = db.Column(db.Integer, nullable=False)
    pickup_location_name = db.Column(db.String(220), nullable=True)
    pickup_borough = db.Column(db.String(80), nullable=True)
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "pickup_location_id", name="uk_taxi_pickup_stats_date_location"),
        db.Index("idx_taxi_pickup_stats_date_count", "stat_date", "trip_count"),
    )


class TaxiDropoffLocationStats(db.Model):
    __tablename__ = "taxi_dropoff_location_stats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False)
    dropoff_location_id = db.Column(db.Integer, nullable=False)
    dropoff_location_name = db.Column(db.String(220), nullable=True)
    dropoff_borough = db.Column(db.String(80), nullable=True)
    trip_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("stat_date", "dropoff_location_id", name="uk_taxi_dropoff_stats_date_location"),
        db.Index("idx_taxi_dropoff_stats_date_count", "stat_date", "trip_count"),
    )


class TaxiStatsMeta(db.Model):
    __tablename__ = "taxi_stats_meta"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stats_name = db.Column(db.String(80), nullable=False, unique=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
    last_rebuild_time = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
