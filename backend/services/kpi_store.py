import sqlite3
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = "backend/races.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===============================
# 예측 결과 기록
# ===============================
def record_prediction(
    race_id: str,
    decision: int,
    confidence: float,
    passed: int,
):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO predictions
        (race_id, predicted_horse_no, confidence, passed, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            race_id,
            decision,
            confidence,
            passed,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


# ===============================
# 실제 결과 기록
# ===============================
def record_result(
    race_id: str,
    winner: int,
    payout: float,
):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO actual_results
        (race_id, winner, payout, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            race_id,
            winner,
            payout,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


# ===============================
# KPI 요약
# ===============================
def summary() -> Dict[str, Any]:
    conn = _get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            p.race_id,
            p.predicted_horse_no AS decision,
            p.confidence,
            p.passed,
            a.winner,
            a.payout
        FROM predictions p
        LEFT JOIN actual_results a
          ON p.race_id = a.race_id
        WHERE p.passed = 0
        """
    ).fetchall()

    total = len(rows)
    hit = 0
    roi_sum = 0.0
    valid = 0

    for r in rows:
        if r["winner"] is None:
            continue

        valid += 1
        if int(r["decision"]) == int(r["winner"]):
            hit += 1
            roi_sum += float(r["payout"])
        else:
            roi_sum -= 1.0

    conn.close()

    return {
        "total_predictions": total,
        "evaluated": valid,
        "hit": hit,
        "hit_rate": (hit / valid) if valid else 0.0,
        "roi": roi_sum,
    }


# ===============================
# CONFIDENCE 구간별 통계
# ===============================
def confidence_bins() -> List[Dict[str, Any]]:
    bins = [
        (0.0, 0.4),
        (0.4, 0.6),
        (0.6, 0.8),
        (0.8, 1.01),
    ]

    conn = _get_conn()
    cur = conn.cursor()

    results = []

    for lo, hi in bins:
        rows = cur.execute(
            """
            SELECT
                p.predicted_horse_no AS decision,
                a.winner
            FROM predictions p
            JOIN actual_results a
              ON p.race_id = a.race_id
            WHERE p.passed = 0
              AND p.confidence >= ?
              AND p.confidence < ?
            """,
            (lo, hi),
        ).fetchall()

        total = len(rows)
        hit = sum(
            1 for r in rows
            if int(r["decision"]) == int(r["winner"])
        )

        results.append({
            "range": f"{lo:.1f} ~ {hi:.1f}",
            "total": total,
            "hit": hit,
            "hit_rate": (hit / total) if total else 0.0,
        })

    conn.close()
    return results


# ===============================
# 예측 히스토리
# ===============================
def get_predict_history(limit: int = 100) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            race_id,
            predicted_horse_no,
            confidence,
            passed,
            updated_at
        FROM predictions
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [
        {
            "race_id": r["race_id"],
            "decision": r["predicted_horse_no"],
            "confidence": r["confidence"],
            "passed": r["passed"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


# ===============================
# 추천 CONFIDENCE 기준선 (🔥 추가)
# ===============================
def recommend_threshold(threshold: float) -> Dict[str, Any]:
    conn = _get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            p.predicted_horse_no AS decision,
            a.winner,
            a.payout
        FROM predictions p
        JOIN actual_results a
          ON p.race_id = a.race_id
        WHERE p.passed = 0
          AND p.confidence >= ?
        """,
        (threshold,),
    ).fetchall()

    hit = 0
    roi = 0.0

    for r in rows:
        if int(r["decision"]) == int(r["winner"]):
            hit += 1
            roi += float(r["payout"])
        else:
            roi -= 1.0

    conn.close()

    total = len(rows)

    return {
        "threshold": threshold,
        "count": total,
        "hit_rate": (hit / total) if total else 0.0,
        "roi": roi,
    }

  
