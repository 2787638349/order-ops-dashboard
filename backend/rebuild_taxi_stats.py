import argparse

from app import create_app
from app.extensions import db
from app.services.taxi_stats_service import parse_date, rebuild_taxi_stats


def main():
    parser = argparse.ArgumentParser(description="Rebuild pre-aggregated taxi analysis stats.")
    parser.add_argument("--start-date", dest="start_date", help="Start date, for example 2025-01-01")
    parser.add_argument("--end-date", dest="end_date", help="End date, for example 2025-01-31")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        result = rebuild_taxi_stats(parse_date(args.start_date), parse_date(args.end_date))
        print(result["message"], flush=True)


if __name__ == "__main__":
    main()
