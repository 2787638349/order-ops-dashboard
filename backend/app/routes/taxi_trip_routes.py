import csv
import io
from datetime import datetime, time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.taxi_trip import TaxiTrip

taxi_trip_bp = Blueprint("taxi_trip", __name__, url_prefix="/api/taxi-trips")


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


def parse_int(value):
    if value in [None, ""]:
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def parse_decimal(value):
    if value in [None, ""]:
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_datetime(value):
    if not value:
        return None

    value = str(value).strip().replace("T", " ")
    if value.endswith("Z"):
        value = value[:-1]
    if "." in value:
        value = value.split(".", 1)[0]

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None


def parse_date_boundary(value, is_end=False):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed:
        return parsed

    try:
        date_value = datetime.strptime(value, "%Y-%m-%d").date()
        return datetime.combine(date_value, time.max if is_end else time.min)
    except ValueError:
        return None


def bool_arg(value):
    if value is None or value == "":
        return None
    value = str(value).strip().lower()
    if value in ["true", "1", "yes", "y"]:
        return True
    if value in ["false", "0", "no", "n"]:
        return False
    return None


def decode_csv_content(file_bytes):
    if file_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ["utf-16", "utf-16le", "utf-16be", "utf-8-sig", "utf-8", "gb18030", "gbk"]
    elif file_bytes[:200].count(b"\x00") > 20:
        encodings = ["utf-16", "utf-16le", "utf-16be", "utf-8-sig", "utf-8", "gb18030", "gbk"]
    else:
        encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16", "utf-16le", "utf-16be"]

    for encoding in encodings:
        try:
            return file_bytes.decode(encoding).replace("\x00", "")
        except UnicodeDecodeError:
            continue

    return file_bytes.decode("utf-8", errors="replace").replace("\x00", "")


def build_csv_reader(content):
    sample = content[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        dialect = csv.excel_tab if delimiter == "\t" else csv.excel

    stream = io.StringIO(content)
    return csv.DictReader(stream, dialect=dialect)


def normalize_row(row):
    normalized = {}
    for key, value in row.items():
        if key is None:
            continue
        clean_key = key.strip().lstrip("\ufeff")
        normalized[clean_key] = value.strip() if isinstance(value, str) else value
    return normalized


def row_value(row, *names):
    lower_map = {key.lower(): value for key, value in row.items()}
    for name in names:
        if name in row:
            return row.get(name)
        value = lower_map.get(name.lower())
        if value is not None:
            return value
    return None


def calculate_duration(pickup_time, dropoff_time):
    if not pickup_time or not dropoff_time:
        return None
    seconds = (dropoff_time - pickup_time).total_seconds()
    return Decimal(str(round(seconds / 60, 2)))


def get_abnormal_reasons(trip):
    reasons = []

    if trip.total_amount is not None and trip.total_amount < 0:
        reasons.append("total_amount < 0")
    if trip.fare_amount is not None and trip.fare_amount < 0:
        reasons.append("fare_amount < 0")
    if trip.trip_distance is not None and trip.trip_distance <= 0:
        reasons.append("trip_distance <= 0")
    if trip.passenger_count is not None and trip.passenger_count <= 0:
        reasons.append("passenger_count <= 0")
    if trip.pickup_time and trip.dropoff_time and trip.pickup_time >= trip.dropoff_time:
        reasons.append("pickup_time >= dropoff_time")
    if trip.trip_duration_min is not None and trip.trip_duration_min <= 0:
        reasons.append("trip_duration_min <= 0")
    if trip.trip_duration_min is not None and trip.trip_duration_min > 720:
        reasons.append("trip_duration_min > 720")
    if trip.trip_distance is not None and trip.trip_distance > 100:
        reasons.append("trip_distance > 100")

    return reasons


def generate_trip_no(pickup_time, sequence):
    date_part = (pickup_time or datetime.now()).strftime("%Y%m%d")
    return f"TAXI{date_part}{sequence:06d}"


def generate_unique_trip_no(pickup_time, sequence):
    while True:
        trip_no = generate_trip_no(pickup_time, sequence)
        if not TaxiTrip.query.filter_by(trip_no=trip_no).first():
            return trip_no, sequence
        sequence += 1


def apply_filters(query):
    trip_no = request.args.get("tripNo", "").strip()
    payment_type = parse_int(request.args.get("paymentType"))
    passenger_count = parse_int(request.args.get("passengerCount"))
    pickup_location_id = parse_int(request.args.get("pickupLocationId"))
    dropoff_location_id = parse_int(request.args.get("dropoffLocationId"))
    start_date = parse_date_boundary(request.args.get("startDate", "").strip())
    end_date = parse_date_boundary(request.args.get("endDate", "").strip(), is_end=True)
    min_distance = parse_decimal(request.args.get("minDistance"))
    max_distance = parse_decimal(request.args.get("maxDistance"))
    min_amount = parse_decimal(request.args.get("minAmount"))
    max_amount = parse_decimal(request.args.get("maxAmount"))
    is_abnormal = bool_arg(request.args.get("isAbnormal"))

    if trip_no:
        query = query.filter(TaxiTrip.trip_no.like(f"%{trip_no}%"))
    if payment_type is not None:
        query = query.filter(TaxiTrip.payment_type == payment_type)
    if passenger_count is not None:
        query = query.filter(TaxiTrip.passenger_count == passenger_count)
    if pickup_location_id is not None:
        query = query.filter(TaxiTrip.pickup_location_id == pickup_location_id)
    if dropoff_location_id is not None:
        query = query.filter(TaxiTrip.dropoff_location_id == dropoff_location_id)
    if start_date:
        query = query.filter(TaxiTrip.pickup_time >= start_date)
    if end_date:
        query = query.filter(TaxiTrip.pickup_time <= end_date)
    if min_distance is not None:
        query = query.filter(TaxiTrip.trip_distance >= min_distance)
    if max_distance is not None:
        query = query.filter(TaxiTrip.trip_distance <= max_distance)
    if min_amount is not None:
        query = query.filter(TaxiTrip.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(TaxiTrip.total_amount <= max_amount)
    if is_abnormal is not None:
        query = query.filter(TaxiTrip.is_abnormal == is_abnormal)

    return query


@taxi_trip_bp.route("", methods=["GET"])
@taxi_trip_bp.route("/", methods=["GET"])
def get_taxi_trips():
    page = parse_int(request.args.get("page")) or 1
    page_size = parse_int(request.args.get("pageSize")) or 10
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)

    query = apply_filters(TaxiTrip.query)

    pagination = query.order_by(TaxiTrip.pickup_time.desc(), TaxiTrip.id.desc()).paginate(
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


@taxi_trip_bp.route("/import", methods=["POST"])
def import_taxi_trips():
    file = request.files.get("file")

    if not file or file.filename == "":
        return fail("请上传 CSV 文件")

    if not file.filename.lower().endswith(".csv"):
        return fail("请上传 CSV 文件")

    try:
        file_bytes = file.stream.read()
        content = decode_csv_content(file_bytes)
        reader = build_csv_reader(content)

        if not reader.fieldnames:
            return fail("CSV 文件为空或表头不正确")

        created_count = 0
        skipped_count = 0
        abnormal_count = 0
        errors = []
        current_file_keys = set()
        max_id = db.session.query(func.coalesce(func.max(TaxiTrip.id), 0)).scalar() or 0
        sequence = int(max_id) + 1

        for index, raw_row in enumerate(reader, start=2):
            row = normalize_row(raw_row)

            pickup_time = parse_datetime(row_value(row, "tpep_pickup_datetime", "pickup_time"))
            dropoff_time = parse_datetime(row_value(row, "tpep_dropoff_datetime", "dropoff_time"))
            pickup_location_id = parse_int(row_value(row, "PULocationID", "pickup_location_id"))
            dropoff_location_id = parse_int(row_value(row, "DOLocationID", "dropoff_location_id"))
            total_amount = parse_decimal(row_value(row, "total_amount"))

            if not pickup_time or not dropoff_time:
                skipped_count += 1
                errors.append(f"第 {index} 行上下车时间格式不正确")
                continue
            if pickup_location_id is None or dropoff_location_id is None:
                skipped_count += 1
                errors.append(f"第 {index} 行上下车区域ID不能为空")
                continue
            if total_amount is None:
                skipped_count += 1
                errors.append(f"第 {index} 行 total_amount 格式不正确")
                continue

            duplicate_key = (
                pickup_time,
                dropoff_time,
                pickup_location_id,
                dropoff_location_id,
                total_amount,
            )

            if duplicate_key in current_file_keys:
                skipped_count += 1
                errors.append(f"第 {index} 行在当前 CSV 中重复")
                continue

            current_file_keys.add(duplicate_key)

            exists = TaxiTrip.query.filter(
                TaxiTrip.pickup_time == pickup_time,
                TaxiTrip.dropoff_time == dropoff_time,
                TaxiTrip.pickup_location_id == pickup_location_id,
                TaxiTrip.dropoff_location_id == dropoff_location_id,
                TaxiTrip.total_amount == total_amount,
            ).first()

            if exists:
                skipped_count += 1
                errors.append(f"第 {index} 行已存在，跳过")
                continue

            trip_no, sequence = generate_unique_trip_no(pickup_time, sequence)
            trip_duration_min = calculate_duration(pickup_time, dropoff_time)
            trip = TaxiTrip(
                trip_no=trip_no,
                vendor_id=parse_int(row_value(row, "VendorID", "vendor_id")),
                pickup_time=pickup_time,
                dropoff_time=dropoff_time,
                passenger_count=parse_int(row_value(row, "passenger_count")),
                trip_distance=parse_decimal(row_value(row, "trip_distance")),
                rate_code_id=parse_int(row_value(row, "RatecodeID", "rate_code_id")),
                store_and_fwd_flag=row_value(row, "store_and_fwd_flag"),
                pickup_location_id=pickup_location_id,
                dropoff_location_id=dropoff_location_id,
                payment_type=parse_int(row_value(row, "payment_type")),
                fare_amount=parse_decimal(row_value(row, "fare_amount")),
                extra=parse_decimal(row_value(row, "extra")),
                mta_tax=parse_decimal(row_value(row, "mta_tax")),
                tip_amount=parse_decimal(row_value(row, "tip_amount")),
                tolls_amount=parse_decimal(row_value(row, "tolls_amount")),
                improvement_surcharge=parse_decimal(row_value(row, "improvement_surcharge")),
                total_amount=total_amount,
                congestion_surcharge=parse_decimal(row_value(row, "congestion_surcharge")),
                airport_fee=parse_decimal(row_value(row, "Airport_fee", "airport_fee")),
                cbd_congestion_fee=parse_decimal(row_value(row, "cbd_congestion_fee")),
                trip_duration_min=trip_duration_min,
            )

            reasons = get_abnormal_reasons(trip)
            if reasons:
                trip.is_abnormal = True
                trip.abnormal_reason = ";".join(reasons)
                abnormal_count += 1

            db.session.add(trip)
            created_count += 1
            sequence += 1

        db.session.commit()

        return success(
            data={
                "createdCount": created_count,
                "skippedCount": skipped_count,
                "abnormalCount": abnormal_count,
                "errors": errors[:200]
            },
            message="导入成功"
        )

    except IntegrityError as e:
        db.session.rollback()
        return fail(f"导入出租车行程失败：存在重复数据或唯一编号冲突，{str(e)}", 500)
    except Exception as e:
        db.session.rollback()
        return fail(f"导入出租车行程失败：{str(e)}", 500)


@taxi_trip_bp.route("/export", methods=["GET"])
def export_taxi_trips():
    query = apply_filters(TaxiTrip.query)
    trips = query.order_by(TaxiTrip.pickup_time.desc(), TaxiTrip.id.desc()).all()

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)

    writer.writerow([
        "tripNo",
        "vendorId",
        "pickupTime",
        "dropoffTime",
        "passengerCount",
        "tripDistance",
        "rateCodeId",
        "storeAndFwdFlag",
        "pickupLocationId",
        "pickupLocationName",
        "dropoffLocationId",
        "dropoffLocationName",
        "paymentType",
        "fareAmount",
        "extra",
        "mtaTax",
        "tipAmount",
        "tollsAmount",
        "improvementSurcharge",
        "totalAmount",
        "congestionSurcharge",
        "airportFee",
        "cbdCongestionFee",
        "tripDurationMin",
        "isAbnormal",
        "abnormalReason",
    ])

    for trip in trips:
        data = trip.to_dict()
        writer.writerow([
            data["tripNo"],
            data["vendorId"],
            data["pickupTime"],
            data["dropoffTime"],
            data["passengerCount"],
            data["tripDistance"],
            data["rateCodeId"],
            data["storeAndFwdFlag"],
            data["pickupLocationId"],
            data["pickupLocationName"],
            data["dropoffLocationId"],
            data["dropoffLocationName"],
            data["paymentType"],
            data["fareAmount"],
            data["extra"],
            data["mtaTax"],
            data["tipAmount"],
            data["tollsAmount"],
            data["improvementSurcharge"],
            data["totalAmount"],
            data["congestionSurcharge"],
            data["airportFee"],
            data["cbdCongestionFee"],
            data["tripDurationMin"],
            "是" if data["isAbnormal"] else "否",
            data["abnormalReason"] or "",
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=taxi_trips_export.csv"
        }
    )
