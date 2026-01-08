# backend/scripts/load_horse_ai_local.py
import argparse
from backend.services.horse_ai import (
    init_horse_tables,
    load_horse_profile_xlsx,
    load_horse_performance_xlsx,
    compute_and_store_horse_scores,
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, help="HorseProfileList*.xlsx path")
    ap.add_argument("--perf", required=True, help="scorePeriod50*.xlsx path")
    ap.add_argument("--period-from", default=None)
    ap.add_argument("--period-to", default=None)
    args = ap.parse_args()

    db_path = init_horse_tables(None)
    print("[DB]", db_path)

    print(load_horse_profile_xlsx(args.profile, db_path))
    print(load_horse_performance_xlsx(args.perf, args.period_from, args.period_to, db_path))
    print(compute_and_store_horse_scores(db_path))

if __name__ == "__main__":
    main()
