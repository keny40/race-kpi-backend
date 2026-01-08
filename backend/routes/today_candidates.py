# backend/routes/today_candidates.py
from fastapi import APIRouter
from backend.services.screener import screen_races
from backend.services.rough_confidence import rough_confidence

router = APIRouter(prefix="/api/today", tags=["today"])

@router.get("/candidates")
def today_candidates():
    races = load_today_races_from_text()   # Text 자료 기반
    screened = screen_races(races)

    results = []
    for r in screened:
        entry_df = load_entry_df(r["race_no"])
        rc = rough_confidence(entry_df)
        results.append({
            "race_no": r["race_no"],
            "rough_conf": rc,
            "status": "PDF_CHECK" if rc >= 0.45 else "PASS"
        })

    return {
        "date": get_today(),
        "candidates": sorted(results, key=lambda x: x["rough_conf"], reverse=True)
    }
