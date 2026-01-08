# backend/routes/kpi_confidence_bins.py
from __future__ import annotations
from fastapi import APIRouter
import sqlite3, os

DB_PATH = os.getenv("DB_PATH", "races.db")
router = APIRouter(prefix="/api/kpi", tags=["kpi"])

BINS = [
    (0.00, 0.55),
    (0.55, 0.60),
    (0.60, 0.65),
    (0.65, 1.01),
]

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/confidence_bins")
def confidence_bins():
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
          json_extract(meta, '$.confidence') AS confidence,
          json_extract(meta, '$.result') AS result
        FROM admin_logs
        WHERE action='ACTUAL'
    """).fetchall()
    conn.close()

    stats = []
    for lo, hi in BINS:
        hit = miss = 0
        for r in rows:
            c = r["confidence"]
            if c is None:
                continue
            c = float(c)
            if lo <= c < hi:
                if r["result"] == "HIT":
                    hit += 1
                elif r["result"] == "MISS":
                    miss += 1
        total = hit + miss
        stats.append({
            "range": f"{lo:.2f}–{hi:.2f}",
            "hit": hit,
            "miss": miss,
            "hit_rate": (hit / total) if total else None,
            "samples": total,
        })

    return {"bins": stats}
