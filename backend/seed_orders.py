import random
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models.order import Order


app = create_app()

cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
locations = ["火车站", "机场", "大学城", "万达广场", "市中心", "科技园", "医院", "写字楼", "地铁站"]
statuses = ["completed", "cancelled", "pending"]
payment_methods = ["微信支付", "支付宝", "银行卡", "余额支付"]


def generate_orders(count=300):
    orders = []

    for i in range(1, count + 1):
        city = random.choice(cities)
        start_location = random.choice(locations)
        end_location = random.choice(locations)

        while end_location == start_location:
            end_location = random.choice(locations)

        order_time = datetime.now() - timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        amount = Decimal(str(round(random.uniform(8, 120), 2)))

        order = Order(
            order_no=f"OD{datetime.now().strftime('%Y%m%d')}{i:06d}",
            user_id=f"U{random.randint(10000, 99999)}",
            city=city,
            start_location=start_location,
            end_location=end_location,
            order_amount=amount,
            order_status=random.choice(statuses),
            payment_method=random.choice(payment_methods),
            order_time=order_time
        )

        orders.append(order)

    return orders


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        Order.query.delete()
        db.session.commit()

        orders = generate_orders(300)
        db.session.add_all(orders)
        db.session.commit()

        print("已成功插入 300 条模拟订单数据")