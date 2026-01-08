# backend/services/kpi.py
import sqlite3
from typing import Dict, Any


def _table_exists(cur, name: str) -> bool:
    r = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return r is not None


def get_kpi_summary(db_path: str) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    has_actual = _table_exists(cur, "actual_results")

    # ==========================
    # MOCK KPI (actual_results 없음)
    # ==========================
    if not has_actual:
        rows = cur.execute("""
            SELECT
                predicted_horse_no,
                confidence,
                passed
            FROM predictions
        """).fetchall()

        total = len(rows)

        bins = {
            "0.0-0.3": {"total": 0},
            "0.3-0.6": {"total": 0},
            "0.6-1.0": {"total": 0},
        }

        for r in rows:
            if r["passed"] == 1:
                continue

            conf = r["confidence"] or 0.0
            if conf < 0.3:
                key = "0.0-0.3"
            elif conf < 0.6:
                key = "0.3-0.6"
            else:
                key = "0.6-1.0"

            bins[key]["total"] += 1

        conn.close()

        return {
            "mode": "MOCK",
            "total": total,
            "hit": None,
            "miss": None,
            "hit_rate": None,
            "by_confidence": bins,
        }

    # ==========================
    # REAL KPI (actual_results 존재)
    # ==========================
    rows = cur.execute("""
        SELECT
            p.predicted_horse_no,
            p.confidence,
            p.passed,
            a.winner
        FROM predictions p
        JOIN actual_results a
          ON p.race_id = a.race_id
    """).fetchall()

    total = len(rows)
    hit = 0

    bins = {
        "0.0-0.3": {"hit": 0, "total": 0},
        "0.3-0.6": {"hit": 0, "total": 0},
        "0.6-1.0": {"hit": 0, "total": 0},
    }

    for r in rows:
        if r["passed"] == 1:
            continue

        conf = r["confidence"] or 0.0
        if conf < 0.3:
            key = "0.0-0.3"
        elif conf < 0.6:
            key = "0.3-0.6"
        else:
            key = "0.6-1.0"

        bins[key]["total"] += 1

        if r["predicted_horse_no"] == r["winner"]:
            hit += 1
            bins[key]["hit"] += 1

    conn.close()

    return {
        "mode": "REAL",
        "total": total,
        "hit": hit,
        "miss": total - hit,
        "hit_rate": round(hit / total, 4) if total else 0.0,
        "by_confidence": bins,
    }
