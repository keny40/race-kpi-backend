from fastapi import APIRouter
import sqlite3
from season import SeasonManager

DB_PATH = "races.db"
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/overview")
def overview():
    s = SeasonManager.get_status()
    conn = _conn()
    cur = conn.cursor()

    total_preds = cur.execute("SELECT COUNT(*) AS c FROM predictions").fetchone()["c"] or 0
    total_with_result = cur.execute(
        "SELECT COUNT(*) AS c FROM predictions p JOIN results r ON p.race_id=r.race_id"
    ).fetchone()["c"] or 0

    conn.close()
    return {"season": s, "totals": {"predictions": total_preds, "predictions_with_result": total_with_result}}

@router.get("/recent")
def recent(limit: int = 50):
    conn = _conn()
    rows = conn.execute(
        """
        SELECT p.id, p.race_id, p.decision, p.confidence, p.created_at, r.winner
        FROM predictions p
        LEFT JOIN results r ON p.race_id = r.race_id
        ORDER BY p.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/models")
def models():
    conn = _conn()
    rows = conn.execute(
        """
        SELECT pm.model_name,
               SUM(CASE WHEN pm.label = r.winner THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS hr,
               COUNT(*) AS n
        FROM prediction_models pm
        JOIN results r ON pm.race_id = r.race_id
        WHERE pm.label != 'PASS'
        GROUP BY pm.model_name
        ORDER BY pm.model_name
        """
    ).fetchall()
    conn.close()
    return [{"model": r["model_name"], "hitrate": round(float(r["hr"]), 3), "n": int(r["n"])} for r in rows]

@router.get("/season/status")
def season_status():
    return SeasonManager.get_status()
