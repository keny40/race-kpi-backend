from __future__ import annotations

import csv
import time
from typing import Dict, Any

CSV_PATH = "backend/data/kra_results_sample.csv"


def fetch_real_race_data() -> Dict[str, Any]:
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        raise RuntimeError("no real race data in CSV")

    # 첫 경주 기준
    base = rows[0]
    rc_date = base["rcDate"]
    meet = base["meet"]
    rc_no = base["rcNo"]

    finishers = sorted(
        [r for r in rows if r["rcDate"] == rc_date and r["meet"] == meet and r["rcNo"] == rc_no],
        key=lambda x: int(x["rank"])
    )

    winner = int(finishers[0]["horseNo"])
    top3 = [int(r["horseNo"]) for r in finishers[:3]]

    return {
        "source": "KRA_OFFICIAL_CSV",
        "race_id": f"kra-{rc_date}-{meet}-{rc_no}",
        "features": {
            "meet": meet,
            "race_no": int(rc_no),
            "winner": winner,
            "top3": top3,
            "field_size": len(finishers),
        },
        "raw": finishers,
        "fetched_at": time.time(),
    }
