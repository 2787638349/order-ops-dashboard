import argparse
import math
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pyarrow.parquet as pq

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.taxi_trip import TaxiTrip


def parse_int(value):
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_decimal(value):
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def calculate_duration(pickup_time, dropoff_time):
    if not pickup_time or not dropoff_time:
        return None
    minutes = (dropoff_time - pickup_time).total_seconds() / 60
    return Decimal(str(round(minutes, 2))).quantize(Decimal("0.01"))


def generate_trip_no(pickup_time, sequence):
    date_part = (pickup_time or datetime.now()).strftime("%Y%m%d")
    return f"TAXI{date_part}{sequence:06d}"


def duplicate_key(row):
    return (
        row["pickup_time"],
        row["dropoff_time"],
        row["pickup_location_id"],
        row["dropoff_location_id"],
        row["total_amount"],
    )


def load_existing_keys():
    keys = set()
    query = db.session.query(
        TaxiTrip.pickup_time,
        TaxiTrip.dropoff_time,
        TaxiTrip.pickup_location_id,
        TaxiTrip.dropoff_location_id,
        TaxiTrip.total_amount,
    ).yield_per(10000)

    for item in query:
        keys.add((
            item.pickup_time,
            item.dropoff_time,
            item.pickup_location_id,
            item.dropoff_location_id,
            parse_decimal(item.total_amount),
        ))

    return keys


def abnormal_reasons(row):
    reasons = []

    if row["total_amount"] is not None and row["total_amount"] < 0:
        reasons.append("total_amount < 0")
    if row["fare_amount"] is not None and row["fare_amount"] < 0:
        reasons.append("fare_amount < 0")
    if row["trip_distance"] is not None and row["trip_distance"] <= 0:
        reasons.append("trip_distance <= 0")
    if row["passenger_count"] is not None and row["passenger_count"] <= 0:
        reasons.append("passenger_count <= 0")
    if row["pickup_time"] and row["dropoff_time"] and row["pickup_time"] >= row["dropoff_time"]:
        reasons.append("pickup_time >= dropoff_time")
    if row["trip_duration_min"] is not None and row["trip_duration_min"] <= 0:
        reasons.append("trip_duration_min <= 0")
    if row["trip_duration_min"] is not None and row["trip_duration_min"] > 720:
        reasons.append("trip_duration_min > 720")
    if row["trip_distance"] is not None and row["trip_distance"] > 100:
        reasons.append("trip_distance > 100")

    return reasons


def import_parquet(file_path, batch_size):
    parquet_file = pq.ParquetFile(file_path)
    total_rows = parquet_file.metadata.num_rows
    now = datetime.now()

    max_id = db.session.query(db.func.coalesce(db.func.max(TaxiTrip.id), 0)).scalar() or 0
    sequence = int(max_id) + 1
    existing_keys = load_existing_keys()

    created_count = 0
    skipped_count = 0
    abnormal_count = 0
    processed_count = 0
    error_samples = []

    columns = [
        "VendorID",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "RatecodeID",
        "store_and_fwd_flag",
        "PULocationID",
        "DOLocationID",
        "payment_type",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "improvement_surcharge",
        "total_amount",
        "congestion_surcharge",
        "Airport_fee",
        "cbd_congestion_fee",
    ]

    for batch in parquet_file.iter_batches(batch_size=batch_size, columns=columns):
        data = batch.to_pydict()
        records = []
        batch_rows = batch.num_rows

        for index in range(batch_rows):
            processed_count += 1

            pickup_time = data["tpep_pickup_datetime"][index]
            dropoff_time = data["tpep_dropoff_datetime"][index]
            pickup_location_id = parse_int(data["PULocationID"][index])
            dropoff_location_id = parse_int(data["DOLocationID"][index])
            total_amount = parse_decimal(data["total_amount"][index])

            if not pickup_time or not dropoff_time:
                skipped_count += 1
                if len(error_samples) < 50:
                    error_samples.append(f"第 {processed_count} 行上下车时间为空")
                continue
            if pickup_location_id is None or dropoff_location_id is None:
                skipped_count += 1
                if len(error_samples) < 50:
                    error_samples.append(f"第 {processed_count} 行上下车区域为空")
                continue
            if total_amount is None:
                skipped_count += 1
                if len(error_samples) < 50:
                    error_samples.append(f"第 {processed_count} 行 total_amount 为空或格式错误")
                continue

            row = {
                "trip_no": generate_trip_no(pickup_time, sequence),
                "vendor_id": parse_int(data["VendorID"][index]),
                "pickup_time": pickup_time,
                "dropoff_time": dropoff_time,
                "passenger_count": parse_int(data["passenger_count"][index]),
                "trip_distance": parse_decimal(data["trip_distance"][index]),
                "rate_code_id": parse_int(data["RatecodeID"][index]),
                "store_and_fwd_flag": data["store_and_fwd_flag"][index],
                "pickup_location_id": pickup_location_id,
                "dropoff_location_id": dropoff_location_id,
                "payment_type": parse_int(data["payment_type"][index]),
                "fare_amount": parse_decimal(data["fare_amount"][index]),
                "extra": parse_decimal(data["extra"][index]),
                "mta_tax": parse_decimal(data["mta_tax"][index]),
                "tip_amount": parse_decimal(data["tip_amount"][index]),
                "tolls_amount": parse_decimal(data["tolls_amount"][index]),
                "improvement_surcharge": parse_decimal(data["improvement_surcharge"][index]),
                "total_amount": total_amount,
                "congestion_surcharge": parse_decimal(data["congestion_surcharge"][index]),
                "airport_fee": parse_decimal(data["Airport_fee"][index]),
                "cbd_congestion_fee": parse_decimal(data["cbd_congestion_fee"][index]),
                "trip_duration_min": calculate_duration(pickup_time, dropoff_time),
                "is_abnormal": False,
                "abnormal_reason": None,
                "created_at": now,
                "updated_at": now,
            }

            key = duplicate_key(row)
            if key in existing_keys:
                skipped_count += 1
                continue
            existing_keys.add(key)

            reasons = abnormal_reasons(row)
            if reasons:
                row["is_abnormal"] = True
                row["abnormal_reason"] = ";".join(reasons)
                abnormal_count += 1

            records.append(row)
            sequence += 1

        if records:
            db.session.bulk_insert_mappings(TaxiTrip, records)
            db.session.commit()

        created_count += len(records)
        print(
            f"processed={processed_count}/{total_rows} "
            f"created={created_count} skipped={skipped_count} abnormal={abnormal_count}",
            flush=True,
        )

    return {
        "totalRows": total_rows,
        "createdCount": created_count,
        "skippedCount": skipped_count,
        "abnormalCount": abnormal_count,
        "errors": error_samples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Parquet file path")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        result = import_parquet(Path(args.file), args.batch_size)
        print(f"done={result}", flush=True)


if __name__ == "__main__":
    main()
