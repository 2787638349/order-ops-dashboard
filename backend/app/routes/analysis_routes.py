from flask import Blueprint
from sqlalchemy import func, case

from app.extensions import db
from app.models.order import Order

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@analysis_bp.route("/summary", methods=["GET"])
def get_summary():
    total_orders = Order.query.count()

    completed_orders = Order.query.filter(Order.order_status == "completed").count()

    total_amount = db.session.query(
        func.coalesce(func.sum(Order.order_amount), 0)
    ).filter(Order.order_status == "completed").scalar()

    avg_amount = 0
    if completed_orders > 0:
        avg_amount = float(total_amount) / completed_orders

    completion_rate = 0
    if total_orders > 0:
        completion_rate = completed_orders / total_orders * 100

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "totalOrders": total_orders,
            "completedOrders": completed_orders,
            "totalAmount": round(float(total_amount), 2),
            "avgAmount": round(avg_amount, 2),
            "completionRate": round(completion_rate, 2)
        }
    }


@analysis_bp.route("/daily-trend", methods=["GET"])
def get_daily_trend():
    results = db.session.query(
        func.date(Order.order_time).label("date"),
        func.count(Order.id).label("order_count"),
        func.coalesce(
            func.sum(
                case(
                    (Order.order_status == "completed", Order.order_amount),
                    else_=0
                )
            ),
            0
        ).label("amount")
    ).group_by(
        func.date(Order.order_time)
    ).order_by(
        func.date(Order.order_time)
    ).all()

    return {
        "code": 200,
        "message": "查询成功",
        "data": [
            {
                "date": str(item.date),
                "orderCount": item.order_count,
                "amount": round(float(item.amount), 2)
            }
            for item in results
        ]
    }


@analysis_bp.route("/city-distribution", methods=["GET"])
def get_city_distribution():
    results = db.session.query(
        Order.city,
        func.count(Order.id).label("order_count"),
        func.coalesce(
            func.sum(
                case(
                    (Order.order_status == "completed", Order.order_amount),
                    else_=0
                )
            ),
            0
        ).label("amount")
    ).group_by(
        Order.city
    ).order_by(
        func.count(Order.id).desc()
    ).all()

    return {
        "code": 200,
        "message": "查询成功",
        "data": [
            {
                "city": item.city,
                "orderCount": item.order_count,
                "amount": round(float(item.amount), 2)
            }
            for item in results
        ]
    }


@analysis_bp.route("/hourly-distribution", methods=["GET"])
def get_hourly_distribution():
    results = db.session.query(
        func.hour(Order.order_time).label("hour"),
        func.count(Order.id).label("order_count")
    ).group_by(
        func.hour(Order.order_time)
    ).order_by(
        func.hour(Order.order_time)
    ).all()

    data_map = {item.hour: item.order_count for item in results}

    data = []
    for hour in range(24):
        data.append({
            "hour": hour,
            "orderCount": data_map.get(hour, 0)
        })

    return {
        "code": 200,
        "message": "查询成功",
        "data": data
    }


@analysis_bp.route("/status-distribution", methods=["GET"])
def get_status_distribution():
    results = db.session.query(
        Order.order_status,
        func.count(Order.id).label("order_count")
    ).group_by(
        Order.order_status
    ).all()

    status_name_map = {
        "completed": "已完成",
        "cancelled": "已取消",
        "pending": "待处理"
    }

    return {
        "code": 200,
        "message": "查询成功",
        "data": [
            {
                "status": item.order_status,
                "statusName": status_name_map.get(item.order_status, item.order_status),
                "orderCount": item.order_count
            }
            for item in results
        ]
    }