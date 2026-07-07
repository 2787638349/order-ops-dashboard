from flask import Flask, request
from flask_cors import CORS

from app.config import Config
from app.extensions import db
from app.routes.order_routes import order_bp
from app.routes.analysis_routes import analysis_bp
from app.routes.auth_routes import auth_bp
from app.routes.taxi_trip_routes import taxi_trip_bp
from app.routes.taxi_analysis_routes import taxi_analysis_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.json.ensure_ascii = False

    CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"]
)

    db.init_app(app)

    @app.before_request
    def check_token():
        if request.method == "OPTIONS":
            return None

        public_paths = [
            "/",
            "/api/auth/login"
        ]

        if request.path in public_paths:
            return None

        if not request.path.startswith("/api/"):
            return None

        auth_header = request.headers.get("Authorization", "")
        query_token = request.args.get("token", "")

        token = ""

        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "", 1)
        elif query_token:
            token = query_token

        if token != Config.ADMIN_TOKEN:
            return {
                "code": 401,
                "message": "未登录或登录已失效",
                "data": None
            }, 401

        return None

    app.register_blueprint(order_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(taxi_trip_bp)
    app.register_blueprint(taxi_analysis_bp)

    @app.route("/")
    def index():
        return {
            "code": 200,
            "message": "订单运营分析后台后端启动成功"
        }

    with app.app_context():
        from app.models.order import Order
        from app.models.taxi_zone import TaxiZone
        from app.models.taxi_trip import TaxiTrip
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
        db.create_all()

    return app
