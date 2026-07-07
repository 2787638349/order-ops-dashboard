from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import foreign

from app.extensions import db
from app.models.taxi_zone import TaxiZone


class TaxiTrip(db.Model):
    __tablename__ = "taxi_trips"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment="行程编号")
    vendor_id = db.Column(db.Integer, nullable=True, comment="供应商ID")
    pickup_time = db.Column(db.DateTime, nullable=False, index=True, comment="上车时间")
    dropoff_time = db.Column(db.DateTime, nullable=False, index=True, comment="下车时间")
    passenger_count = db.Column(db.Integer, nullable=True, index=True, comment="乘客数")
    trip_distance = db.Column(db.Numeric(10, 2), nullable=True, comment="行程距离")
    rate_code_id = db.Column(db.Integer, nullable=True, comment="费率代码")
    store_and_fwd_flag = db.Column(db.String(10), nullable=True, comment="暂存转发标记")
    pickup_location_id = db.Column(db.Integer, nullable=False, index=True, comment="上车区域ID")
    dropoff_location_id = db.Column(db.Integer, nullable=False, index=True, comment="下车区域ID")
    payment_type = db.Column(db.Integer, nullable=True, index=True, comment="支付方式")
    fare_amount = db.Column(db.Numeric(10, 2), nullable=True, comment="车费")
    extra = db.Column(db.Numeric(10, 2), nullable=True, comment="额外费用")
    mta_tax = db.Column(db.Numeric(10, 2), nullable=True, comment="MTA税")
    tip_amount = db.Column(db.Numeric(10, 2), nullable=True, comment="小费")
    tolls_amount = db.Column(db.Numeric(10, 2), nullable=True, comment="过路费")
    improvement_surcharge = db.Column(db.Numeric(10, 2), nullable=True, comment="改善附加费")
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, index=True, comment="总金额")
    congestion_surcharge = db.Column(db.Numeric(10, 2), nullable=True, comment="拥堵费")
    airport_fee = db.Column(db.Numeric(10, 2), nullable=True, comment="机场费")
    cbd_congestion_fee = db.Column(db.Numeric(10, 2), nullable=True, comment="CBD拥堵费")
    trip_duration_min = db.Column(db.Numeric(10, 2), nullable=True, comment="行程时长(分钟)")
    is_abnormal = db.Column(db.Boolean, nullable=False, default=False, index=True, comment="是否异常")
    abnormal_reason = db.Column(db.String(500), nullable=True, comment="异常原因")
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    pickup_zone = db.relationship(
        "TaxiZone",
        primaryjoin=lambda: foreign(TaxiTrip.pickup_location_id) == TaxiZone.location_id,
        viewonly=True,
        lazy="joined",
    )
    dropoff_zone = db.relationship(
        "TaxiZone",
        primaryjoin=lambda: foreign(TaxiTrip.dropoff_location_id) == TaxiZone.location_id,
        viewonly=True,
        lazy="joined",
    )

    __table_args__ = (
        db.Index(
            "idx_taxi_trip_duplicate",
            "pickup_time",
            "dropoff_time",
            "pickup_location_id",
            "dropoff_location_id",
            "total_amount",
        ),
        db.Index("idx_taxi_trip_distance", "trip_distance"),
        db.Index("idx_taxi_trip_normal_pickup_distance", "is_abnormal", "pickup_time", "trip_distance"),
        db.Index("idx_taxi_trip_normal_distance_pickup", "is_abnormal", "trip_distance", "pickup_time"),
        db.Index("idx_taxi_trip_payment_pickup", "payment_type", "pickup_time"),
        db.Index("idx_taxi_trip_passenger_pickup", "passenger_count", "pickup_time"),
        db.Index("idx_taxi_trip_pickup_location_time", "pickup_location_id", "pickup_time"),
        db.Index("idx_taxi_trip_dropoff_location_time", "dropoff_location_id", "pickup_time"),
    )

    @staticmethod
    def _format_datetime(value):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None

    @staticmethod
    def _format_decimal(value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _zone_to_dict(zone):
        return zone.to_dict() if zone else None

    def to_dict(self):
        pickup_zone = self._zone_to_dict(self.pickup_zone)
        dropoff_zone = self._zone_to_dict(self.dropoff_zone)

        return {
            "id": self.id,
            "tripNo": self.trip_no,
            "vendorId": self.vendor_id,
            "pickupTime": self._format_datetime(self.pickup_time),
            "dropoffTime": self._format_datetime(self.dropoff_time),
            "passengerCount": self.passenger_count,
            "tripDistance": self._format_decimal(self.trip_distance),
            "rateCodeId": self.rate_code_id,
            "storeAndFwdFlag": self.store_and_fwd_flag,
            "pickupLocationId": self.pickup_location_id,
            "pickupZoneName": pickup_zone["zone"] if pickup_zone else None,
            "pickupBorough": pickup_zone["borough"] if pickup_zone else None,
            "pickupServiceZone": pickup_zone["serviceZone"] if pickup_zone else None,
            "pickupLocationName": pickup_zone["displayName"] if pickup_zone else str(self.pickup_location_id),
            "pickupZone": pickup_zone,
            "dropoffLocationId": self.dropoff_location_id,
            "dropoffZoneName": dropoff_zone["zone"] if dropoff_zone else None,
            "dropoffBorough": dropoff_zone["borough"] if dropoff_zone else None,
            "dropoffServiceZone": dropoff_zone["serviceZone"] if dropoff_zone else None,
            "dropoffLocationName": dropoff_zone["displayName"] if dropoff_zone else str(self.dropoff_location_id),
            "dropoffZone": dropoff_zone,
            "paymentType": self.payment_type,
            "fareAmount": self._format_decimal(self.fare_amount),
            "extra": self._format_decimal(self.extra),
            "mtaTax": self._format_decimal(self.mta_tax),
            "tipAmount": self._format_decimal(self.tip_amount),
            "tollsAmount": self._format_decimal(self.tolls_amount),
            "improvementSurcharge": self._format_decimal(self.improvement_surcharge),
            "totalAmount": self._format_decimal(self.total_amount),
            "congestionSurcharge": self._format_decimal(self.congestion_surcharge),
            "airportFee": self._format_decimal(self.airport_fee),
            "cbdCongestionFee": self._format_decimal(self.cbd_congestion_fee),
            "tripDurationMin": self._format_decimal(self.trip_duration_min),
            "isAbnormal": self.is_abnormal,
            "abnormalReason": self.abnormal_reason,
            "createdAt": self._format_datetime(self.created_at),
            "updatedAt": self._format_datetime(self.updated_at),
        }
