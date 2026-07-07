from datetime import datetime
from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    order_no = db.Column(db.String(50), unique=True, nullable=False, comment="订单编号")
    user_id = db.Column(db.String(50), nullable=False, comment="用户ID")

    city = db.Column(db.String(50), nullable=False, comment="城市")
    start_location = db.Column(db.String(100), nullable=False, comment="起点")
    end_location = db.Column(db.String(100), nullable=False, comment="终点")

    order_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment="订单金额")
    order_status = db.Column(db.String(20), nullable=False, default="completed", comment="订单状态")

    payment_method = db.Column(db.String(30), nullable=True, comment="支付方式")
    order_time = db.Column(db.DateTime, nullable=False, comment="下单时间")

    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "orderNo": self.order_no,
            "userId": self.user_id,
            "city": self.city,
            "startLocation": self.start_location,
            "endLocation": self.end_location,
            "orderAmount": float(self.order_amount),
            "orderStatus": self.order_status,
            "paymentMethod": self.payment_method,
            "orderTime": self.order_time.strftime("%Y-%m-%d %H:%M:%S") if self.order_time else None,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }