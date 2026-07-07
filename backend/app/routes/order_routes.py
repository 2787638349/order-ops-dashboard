import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.order import Order

order_bp = Blueprint("order", __name__, url_prefix="/api/orders")


def success(data=None, message="操作成功"):
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def fail(message="操作失败", code=400):
    return {
        "code": code,
        "message": message,
        "data": None
    }, code


def parse_order_time(value):
    if not value:
        return None

    value = value.replace("T", " ")

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None


def parse_amount(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


@order_bp.route("", methods=["GET"])
@order_bp.route("/", methods=["GET"])
def get_orders():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 10))

    order_no = request.args.get("orderNo", "").strip()
    city = request.args.get("city", "").strip()
    order_status = request.args.get("orderStatus", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()

    query = Order.query

    if order_no:
        query = query.filter(Order.order_no.like(f"%{order_no}%"))

    if city:
        query = query.filter(Order.city.like(f"%{city}%"))

    if order_status:
        query = query.filter(Order.order_status == order_status)

    if start_date:
        query = query.filter(Order.order_time >= f"{start_date} 00:00:00")

    if end_date:
        query = query.filter(Order.order_time <= f"{end_date} 23:59:59")

    pagination = query.order_by(Order.order_time.desc()).paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    return success(
        data={
            "list": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "pageSize": page_size
        },
        message="查询成功"
    )

@order_bp.route("/export", methods=["GET"])
def export_orders():
    order_no = request.args.get("orderNo", "").strip()
    city = request.args.get("city", "").strip()
    order_status = request.args.get("orderStatus", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()

    query = Order.query

    if order_no:
        query = query.filter(Order.order_no.like(f"%{order_no}%"))

    if city:
        query = query.filter(Order.city.like(f"%{city}%"))

    if order_status:
        query = query.filter(Order.order_status == order_status)

    if start_date:
        query = query.filter(Order.order_time >= f"{start_date} 00:00:00")

    if end_date:
        query = query.filter(Order.order_time <= f"{end_date} 23:59:59")

    orders = query.order_by(Order.order_time.desc()).all()

    output = io.StringIO()

    # 写入 UTF-8 BOM，避免 Excel 打开中文乱码
    output.write("\ufeff")

    writer = csv.writer(output)

    writer.writerow([
        "orderNo",
        "userId",
        "city",
        "startLocation",
        "endLocation",
        "orderAmount",
        "orderStatus",
        "paymentMethod",
        "orderTime",
    ])

    for order in orders:
        writer.writerow([
            order.order_no,
            order.user_id,
            order.city,
            order.start_location,
            order.end_location,
            float(order.order_amount),
            order.order_status,
            order.payment_method or "",
            order.order_time.strftime("%Y-%m-%d %H:%M:%S") if order.order_time else "",
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=orders_export.csv"
        }
    )

@order_bp.route("/<int:order_id>", methods=["GET"])
def get_order_detail(order_id):
    order = Order.query.get(order_id)

    if not order:
        return fail("订单不存在", 404)

    return success(order.to_dict(), "查询成功")


@order_bp.route("", methods=["POST"])
@order_bp.route("/", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "orderNo",
        "userId",
        "city",
        "startLocation",
        "endLocation",
        "orderAmount",
        "orderStatus",
        "orderTime"
    ]

    for field in required_fields:
        if data.get(field) in [None, ""]:
            return fail(f"{field} 不能为空")

    order_amount = parse_amount(data.get("orderAmount"))
    if order_amount is None:
        return fail("订单金额格式不正确")

    order_time = parse_order_time(data.get("orderTime"))
    if order_time is None:
        return fail("下单时间格式不正确")

    order = Order(
        order_no=data.get("orderNo"),
        user_id=data.get("userId"),
        city=data.get("city"),
        start_location=data.get("startLocation"),
        end_location=data.get("endLocation"),
        order_amount=order_amount,
        order_status=data.get("orderStatus"),
        payment_method=data.get("paymentMethod"),
        order_time=order_time
    )

    try:
        db.session.add(order)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return fail("订单编号已存在")
    except Exception as e:
        db.session.rollback()
        return fail(f"新增订单失败：{str(e)}", 500)

    return success(order.to_dict(), "新增订单成功")


@order_bp.route("/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    order = Order.query.get(order_id)

    if not order:
        return fail("订单不存在", 404)

    data = request.get_json(silent=True) or {}

    if "orderNo" in data:
        order.order_no = data.get("orderNo")

    if "userId" in data:
        order.user_id = data.get("userId")

    if "city" in data:
        order.city = data.get("city")

    if "startLocation" in data:
        order.start_location = data.get("startLocation")

    if "endLocation" in data:
        order.end_location = data.get("endLocation")

    if "orderAmount" in data:
        order_amount = parse_amount(data.get("orderAmount"))
        if order_amount is None:
            return fail("订单金额格式不正确")
        order.order_amount = order_amount

    if "orderStatus" in data:
        order.order_status = data.get("orderStatus")

    if "paymentMethod" in data:
        order.payment_method = data.get("paymentMethod")

    if "orderTime" in data:
        order_time = parse_order_time(data.get("orderTime"))
        if order_time is None:
            return fail("下单时间格式不正确")
        order.order_time = order_time

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return fail("订单编号已存在")
    except Exception as e:
        db.session.rollback()
        return fail(f"修改订单失败：{str(e)}", 500)

    return success(order.to_dict(), "修改订单成功")

@order_bp.route("/import", methods=["POST"])
def import_orders():
    file = request.files.get("file")

    if not file or file.filename == "":
        return fail("请上传 CSV 文件")

    if not file.filename.lower().endswith(".csv"):
        return fail("请上传 CSV 文件")

    try:
        file_bytes = file.stream.read()

        encodings = [
            "utf-8-sig",
            "utf-8",
            "gb18030",
            "gbk",
            "utf-16",
            "utf-16le",
            "utf-16be",
        ]

        content = None

        for encoding in encodings:
            try:
                content = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            content = file_bytes.decode("utf-8", errors="replace")

        stream = io.StringIO(content)
        reader = csv.DictReader(stream)

        if not reader.fieldnames:
            return fail("CSV 文件为空或表头不正确")

        created_count = 0
        skipped_count = 0
        errors = []

        # 用来防止同一个 CSV 文件内部订单编号重复
        current_file_order_nos = set()

        for index, row in enumerate(reader, start=2):
            order_no = (row.get("orderNo") or row.get("order_no") or "").strip()

            if not order_no:
                skipped_count += 1
                errors.append(f"第 {index} 行订单编号为空")
                continue

            # 3. 判断 CSV 内部是否重复
            if order_no in current_file_order_nos:
                skipped_count += 1
                errors.append(f"第 {index} 行订单编号 {order_no} 在 CSV 中重复")
                continue

            current_file_order_nos.add(order_no)

            # 4. 判断数据库中是否已经存在
            exists = Order.query.filter_by(order_no=order_no).first()
            if exists:
                skipped_count += 1
                errors.append(f"订单编号 {order_no} 已存在")
                continue

            order_amount = parse_amount(row.get("orderAmount") or row.get("order_amount"))
            order_time = parse_order_time(row.get("orderTime") or row.get("order_time"))

            if order_amount is None:
                skipped_count += 1
                errors.append(f"订单编号 {order_no} 的金额格式不正确")
                continue

            if order_time is None:
                skipped_count += 1
                errors.append(f"订单编号 {order_no} 的时间格式不正确")
                continue

            order = Order(
                order_no=order_no,
                user_id=(row.get("userId") or row.get("user_id") or "").strip(),
                city=(row.get("city") or "").strip(),
                start_location=(row.get("startLocation") or row.get("start_location") or "").strip(),
                end_location=(row.get("endLocation") or row.get("end_location") or "").strip(),
                order_amount=order_amount,
                order_status=(row.get("orderStatus") or row.get("order_status") or "completed").strip(),
                payment_method=(row.get("paymentMethod") or row.get("payment_method") or "").strip() or None,
                order_time=order_time
            )

            db.session.add(order)
            created_count += 1

        db.session.commit()

        return success(
            data={
                "createdCount": created_count,
                "skippedCount": skipped_count,
                "errors": errors
            },
            message="导入成功"
        )

    except Exception as e:
        db.session.rollback()
        return fail(f"导入订单失败：{str(e)}", 500)


@order_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = Order.query.get(order_id)

    if not order:
        return fail("订单不存在", 404)

    try:
        db.session.delete(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return fail(f"删除订单失败：{str(e)}", 500)

    return success(None, "删除订单成功")