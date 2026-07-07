from datetime import datetime

from app.extensions import db


class TaxiZone(db.Model):
    __tablename__ = "taxi_zones"

    location_id = db.Column(db.Integer, primary_key=True, comment="TLC LocationID")
    borough = db.Column(db.String(80), nullable=True, index=True, comment="行政区")
    zone = db.Column(db.String(120), nullable=True, index=True, comment="区域名称")
    service_zone = db.Column(db.String(80), nullable=True, comment="服务区域")
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    @property
    def display_name(self):
        if self.zone and self.borough:
            return f"{self.zone} ({self.borough})"
        return self.zone or self.borough or str(self.location_id)

    def to_dict(self):
        return {
            "locationId": self.location_id,
            "borough": self.borough,
            "zone": self.zone,
            "serviceZone": self.service_zone,
            "displayName": self.display_name,
        }
