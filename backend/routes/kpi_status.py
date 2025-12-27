from fastapi import APIRouter
from datetime import datetime, timedelta
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api/kpi/status", tags=["kpi-status"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _recent_accuracy(window: int = 20) -> float:
    """
    최근 예측 정확도 계산
    HIT / (HIT + MISS)
    """
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            p.decision,
            a.winner
        FROM predictions p
        JOIN race_actuals a
          ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT ?
    """, (window,)).fetchall()

    conn.close()

    hit = 0
    miss = 0

    for r in rows:
        if r["decision"] == "PASS":
            continue
        if r["decision"] == r["winner"]:
            hit += 1
        else:
            miss += 1

    if hit + miss == 0:
        return 1.0

    return hit / (hit + miss)


# --------------------------------------------------
# ✅ 핵심: predict.py에서 사용하는 표준 함수
# --------------------------------------------------
def get_current_status() -> str:
    """
    현재 KPI 상태 반환
    - GREEN / YELLOW / RED
    """
    acc = _recent_accuracy(window=20)

    if acc >= 0.65:
        return "GREEN"
    if acc >= 0.55:
        return "YELLOW"
    return "RED"


# --------------------------------------------------
# (선택) API로도 조회 가능
# --------------------------------------------------
@router.get("")
def api_status():
    return {
        "status": get_current_status(),
        "checked_at": datetime.utcnow().isoformat()
    }
