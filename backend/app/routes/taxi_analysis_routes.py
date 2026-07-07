import threading
from datetime import datetime, timedelta

from flask import Blueprint, current_app, request
from sqlalchemy import func

from app.extensions import db
from app.models.taxi_stats import (
    TaxiDailyStats,
    TaxiDistanceStats,
    TaxiDropoffLocationStats,
    TaxiHourlyStats,
    TaxiPassengerStats,
    TaxiPaymentStats,
    TaxiPickupLocationStats,
    TaxiStatsMeta,
)
from app.services.taxi_stats_service import rebuild_taxi_stats

taxi_analysis_bp = Blueprint("taxi_analysis", __name__, url_prefix="/api/taxi-analysis")

DEFAULT_ANALYSIS_DAYS = 7
STATS_NOT_READY_MESSAGE = "统计数据尚未生成，请先执行 python rebuild_taxi_stats.py"
STATS_REFRESH_RUNNING_MESSAGE = "聚合统计正在刷新中，请稍后再试"
stats_refresh_lock = threading.Lock()


def success(data=None, message="查询成功"):
    return {
        "code": 200,
        "message": message,
        "data": data,
    }


def business_error(message=STATS_NOT_READY_MESSAGE):
    return {
        "code": 400,
        "message": message,
        "data": None,
    }


def money(value):
    return round(float(value or 0), 2)


def number(value):
    return round(float(value or 0), 2)


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()
    if not value:
        return None

    for date_format in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], date_format).date()
        except ValueError:
            continue
    return None


def has_stats_data():
    return (db.session.query(func.count(TaxiDailyStats.id)).scalar() or 0) > 0


def require_stats_data():
    if not has_stats_data():
        return business_error()
    return None


def get_analysis_date_range():
    start_date = parse_date(request.args.get("startDate"))
    end_date = parse_date(request.args.get("endDate"))

    if start_date and end_date:
        return start_date, end_date

    latest_stat_date = db.session.query(func.max(TaxiDailyStats.stat_date)).scalar()
    if latest_stat_date is None:
        today = datetime.now().date()
        latest_stat_date = today

    if end_date is None:
        end_date = latest_stat_date

    if start_date is None:
        start_date = end_date - timedelta(days=DEFAULT_ANALYSIS_DAYS - 1)

    return start_date, end_date


def apply_stat_date_range(query, model, start_date, end_date):
    return query.filter(
        model.stat_date >= start_date,
        model.stat_date <= end_date,
    )


@taxi_analysis_bp.route("/stats-status", methods=["GET"])
def get_stats_status():
    meta = TaxiStatsMeta.query.filter_by(stats_name="taxi_analysis").first()
    stats_ready = has_stats_data()

    if not meta and not stats_ready:
        return success({
            "status": "empty",
            "lastRebuildTime": None,
            "message": STATS_NOT_READY_MESSAGE,
        })

    return success({
        "status": meta.status if meta else "completed",
        "lastRebuildTime": meta.last_rebuild_time.strftime("%Y-%m-%d %H:%M:%S") if meta and meta.last_rebuild_time else None,
        "message": meta.message if meta and meta.message else ("统计数据已生成" if stats_ready else STATS_NOT_READY_MESSAGE),
    })


def run_stats_refresh(app):
    try:
        with app.app_context():
            rebuild_taxi_stats()
    finally:
        stats_refresh_lock.release()


@taxi_analysis_bp.route("/stats-refresh", methods=["POST"])
def refresh_stats():
    if not stats_refresh_lock.acquire(blocking=False):
        return business_error(STATS_REFRESH_RUNNING_MESSAGE)

    try:
        app = current_app._get_current_object()
        refresh_thread = threading.Thread(target=run_stats_refresh, args=(app,), daemon=True)
        refresh_thread.start()
    except Exception:
        stats_refresh_lock.release()
        raise

    return success({"status": "running"}, "聚合统计刷新已开始")


@taxi_analysis_bp.route("/summary", methods=["GET"])
def get_summary():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    row = apply_stat_date_range(
        db.session.query(
            func.coalesce(func.sum(TaxiDailyStats.total_trips), 0),
            func.coalesce(func.sum(TaxiDailyStats.normal_trips), 0),
            func.coalesce(func.sum(TaxiDailyStats.abnormal_trips), 0),
            func.coalesce(func.sum(TaxiDailyStats.total_amount), 0),
            func.coalesce(func.sum(TaxiDailyStats.fare_amount), 0),
            func.coalesce(func.sum(TaxiDailyStats.tip_amount), 0),
            func.coalesce(func.sum(TaxiDailyStats.total_distance), 0),
            func.coalesce(func.sum(TaxiDailyStats.total_duration), 0),
        ),
        TaxiDailyStats,
        start_date,
        end_date,
    ).first()

    total_trips, normal_trips, abnormal_trips, total_amount, fare_amount, tip_amount, total_distance, total_duration = row
    total_trips = int(total_trips or 0)
    normal_trips = int(normal_trips or 0)

    avg_amount = float(total_amount or 0) / total_trips if total_trips else 0
    avg_distance = float(total_distance or 0) / normal_trips if normal_trips else 0
    avg_duration = float(total_duration or 0) / normal_trips if normal_trips else 0
    tip_rate = float(tip_amount or 0) / float(fare_amount or 0) * 100 if fare_amount else 0

    return success({
        "totalTrips": total_trips,
        "normalTrips": normal_trips,
        "abnormalTrips": int(abnormal_trips or 0),
        "totalAmount": money(total_amount),
        "avgAmount": money(avg_amount),
        "avgDistance": number(avg_distance),
        "avgDuration": number(avg_duration),
        "tipRate": number(tip_rate),
    })


@taxi_analysis_bp.route("/daily-trend", methods=["GET"])
def get_daily_trend():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        TaxiDailyStats.query,
        TaxiDailyStats,
        start_date,
        end_date,
    ).order_by(TaxiDailyStats.stat_date).all()

    return success([
        {
            "date": item.stat_date.strftime("%Y-%m-%d"),
            "tripCount": int(item.total_trips or 0),
            "totalAmount": money(item.total_amount),
        }
        for item in rows
    ])


@taxi_analysis_bp.route("/hourly-distribution", methods=["GET"])
def get_hourly_distribution():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiHourlyStats.hour,
            func.coalesce(func.sum(TaxiHourlyStats.trip_count), 0).label("trip_count"),
        ),
        TaxiHourlyStats,
        start_date,
        end_date,
    ).group_by(TaxiHourlyStats.hour).all()

    data_map = {int(item.hour): int(item.trip_count or 0) for item in rows if item.hour is not None}

    return success([
        {
            "hour": hour,
            "tripCount": data_map.get(hour, 0),
        }
        for hour in range(24)
    ])


@taxi_analysis_bp.route("/payment-distribution", methods=["GET"])
def get_payment_distribution():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiPaymentStats.payment_type,
            func.max(TaxiPaymentStats.payment_name).label("payment_name"),
            func.coalesce(func.sum(TaxiPaymentStats.trip_count), 0).label("trip_count"),
        ),
        TaxiPaymentStats,
        start_date,
        end_date,
    ).group_by(TaxiPaymentStats.payment_type).order_by(func.sum(TaxiPaymentStats.trip_count).desc()).all()

    return success([
        {
            "paymentType": item.payment_type,
            "paymentName": item.payment_name,
            "tripCount": int(item.trip_count or 0),
        }
        for item in rows
    ])


@taxi_analysis_bp.route("/passenger-distribution", methods=["GET"])
def get_passenger_distribution():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiPassengerStats.passenger_count,
            func.coalesce(func.sum(TaxiPassengerStats.trip_count), 0).label("trip_count"),
        ),
        TaxiPassengerStats,
        start_date,
        end_date,
    ).group_by(TaxiPassengerStats.passenger_count).order_by(TaxiPassengerStats.passenger_count).all()

    return success([
        {
            "passengerCount": item.passenger_count,
            "tripCount": int(item.trip_count or 0),
        }
        for item in rows
    ])


@taxi_analysis_bp.route("/pickup-location-top", methods=["GET"])
def get_pickup_location_top():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiPickupLocationStats.pickup_location_id,
            func.max(TaxiPickupLocationStats.pickup_location_name).label("pickup_location_name"),
            func.max(TaxiPickupLocationStats.pickup_borough).label("pickup_borough"),
            func.coalesce(func.sum(TaxiPickupLocationStats.trip_count), 0).label("trip_count"),
        ),
        TaxiPickupLocationStats,
        start_date,
        end_date,
    ).group_by(TaxiPickupLocationStats.pickup_location_id).order_by(func.sum(TaxiPickupLocationStats.trip_count).desc()).limit(10).all()

    return success([
        {
            "pickupLocationId": item.pickup_location_id,
            "pickupLocationName": item.pickup_location_name or str(item.pickup_location_id),
            "pickupBorough": item.pickup_borough,
            "tripCount": int(item.trip_count or 0),
        }
        for item in rows
    ])


@taxi_analysis_bp.route("/dropoff-location-top", methods=["GET"])
def get_dropoff_location_top():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiDropoffLocationStats.dropoff_location_id,
            func.max(TaxiDropoffLocationStats.dropoff_location_name).label("dropoff_location_name"),
            func.max(TaxiDropoffLocationStats.dropoff_borough).label("dropoff_borough"),
            func.coalesce(func.sum(TaxiDropoffLocationStats.trip_count), 0).label("trip_count"),
        ),
        TaxiDropoffLocationStats,
        start_date,
        end_date,
    ).group_by(TaxiDropoffLocationStats.dropoff_location_id).order_by(func.sum(TaxiDropoffLocationStats.trip_count).desc()).limit(10).all()

    return success([
        {
            "dropoffLocationId": item.dropoff_location_id,
            "dropoffLocationName": item.dropoff_location_name or str(item.dropoff_location_id),
            "dropoffBorough": item.dropoff_borough,
            "tripCount": int(item.trip_count or 0),
        }
        for item in rows
    ])


@taxi_analysis_bp.route("/distance-distribution", methods=["GET"])
def get_distance_distribution():
    not_ready = require_stats_data()
    if not_ready:
        return not_ready

    start_date, end_date = get_analysis_date_range()
    rows = apply_stat_date_range(
        db.session.query(
            TaxiDistanceStats.distance_range,
            TaxiDistanceStats.range_order,
            func.coalesce(func.sum(TaxiDistanceStats.trip_count), 0).label("trip_count"),
        ),
        TaxiDistanceStats,
        start_date,
        end_date,
    ).group_by(TaxiDistanceStats.distance_range, TaxiDistanceStats.range_order).all()

    data_map = {item.distance_range: int(item.trip_count or 0) for item in rows}
    ordered_ranges = ["0-1", "1-3", "3-5", "5-10", "10-20", "20+"]

    return success([
        {
            "range": distance_range,
            "tripCount": data_map.get(distance_range, 0),
        }
        for distance_range in ordered_ranges
    ])
