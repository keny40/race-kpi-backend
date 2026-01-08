from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import io
import csv
from backend.services.db import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/report.csv")
def kpi_report_csv():
    """
    RUN만 CSV로 내보내기
    """
    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, race_id, predicted_horse_no, confidence, created_at
          FROM predictions
         WHERE passed=0
         ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "race_id", "predicted_horse_no", "confidence", "created_at"])
    for r in rows:
        w.writerow([r["id"], r["race_id"], r["predicted_horse_no"], r["confidence"], r["created_at"]])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kpi_run_only.csv"},
    )
