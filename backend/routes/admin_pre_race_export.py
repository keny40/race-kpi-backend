# backend/routes/admin_pre_race_export.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv, io
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-export"])

@router.get("/report/csv")
def export_csv():
    conn = get_conn()
    rows = conn.execute("""
      SELECT race_id, run_at, confidence, decision
      FROM pre_race_run_history
      ORDER BY run_at DESC
    """).fetchall()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["race_id","run_at","confidence","decision"])
    for r in rows:
        w.writerow([r["race_id"], r["run_at"], r["confidence"], r["decision"]])

    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv")
