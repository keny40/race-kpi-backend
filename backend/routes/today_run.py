from fastapi import APIRouter
from backend.services.pdf_parser import parse_today_pdf
from backend.services.slack_notify import notify_slack

router = APIRouter(prefix="/api/today", tags=["today"])

@router.post("/run")
def run_today():
    df = parse_today_pdf("data/s_run_hr_260103_01.pdf")

    results = []
    for race_no, g in df.groupby("race_no"):
        rough_conf = min(0.9, 0.4 + len(g) * 0.02)
        if rough_conf >= 0.55:
            results.append({
                "race_no": race_no,
                "rough_conf": round(rough_conf, 2)
            })

    notify_slack(results)
    return {
        "races": df["race_no"].nunique(),
        "candidates": results
    }
