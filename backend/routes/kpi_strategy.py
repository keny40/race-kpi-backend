# backend/routes/kpi_strategy.py
from fastapi import APIRouter, Request, HTTPException, Query
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

router = APIRouter(prefix="/api/admin/kpi", tags=["kpi-strategy"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
DB_PATH = "races.db"


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/strategy")
def kpi_by_strategy(
    request: Request,
    limit: int = Query(100, ge=20, le=500),
):
    """
    전략별 최근 성과
    - 시계열: hit, roi
    - 요약: hit_rate, avg_roi, count
    """
    _auth(request)

    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            p.strategy,
            p.decision,
            p.roi,
            p.created_at,
            a.winner
        FROM predictions p
        LEFT JOIN actual_results a
          ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    series = defaultdict(list)
    summary = defaultdict(lambda: {"hit": 0, "total": 0, "roi_sum": 0.0})

    for r in reversed(rows):
        strat = r["strategy"] or "UNKNOWN"
        hit = (
            1
            if r["decision"] is not None
            and r["winner"] is not None
            and str(r["decision"]) == str(r["winner"])
            else 0
        )
        roi = float(r["roi"]) if r["roi"] is not None else 1.0

        ts = r["created_at"]
        try:
            ts = datetime.fromisoformat(ts).strftime("%m-%d %H:%M")
        except Exception:
            pass

        series[strat].append({
            "t": ts,
            "hit": hit,
            "roi": roi,
        })

        summary[strat]["hit"] += hit
        summary[strat]["total"] += 1
        summary[strat]["roi_sum"] += roi

    summary_out = []
    for strat, s in summary.items():
        total = s["total"] or 1
        summary_out.append({
            "strategy": strat,
            "count": total,
            "hit_rate": round(s["hit"] / total, 3),
            "avg_roi": round(s["roi_sum"] / total, 3),
        })

    return {
        "limit": limit,
        "series": series,
        "summary": sorted(summary_out, key=lambda x: (-x["hit_rate"], -x["avg_roi"])),
    }
