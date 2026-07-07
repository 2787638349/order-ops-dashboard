import csv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.taxi_zone import TaxiZone


def import_taxi_zones(file_path):
    created_count = 0
    updated_count = 0

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            location_id = int(row["LocationID"])
            zone = db.session.get(TaxiZone, location_id)

            if zone is None:
                zone = TaxiZone(location_id=location_id)
                db.session.add(zone)
                created_count += 1
            else:
                updated_count += 1

            zone.borough = (row.get("Borough") or "").strip() or None
            zone.zone = (row.get("Zone") or "").strip() or None
            zone.service_zone = (row.get("service_zone") or "").strip() or None

    db.session.commit()

    return {
        "createdCount": created_count,
        "updatedCount": updated_count,
        "totalCount": TaxiZone.query.count(),
    }


def main():
    file_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DIR / "data" / "taxi_zone_lookup.csv"
    app = create_app()

    with app.app_context():
        result = import_taxi_zones(file_path)
        print(result)


if __name__ == "__main__":
    main()
