# backend/services/recent_roi.py
import sqlite3
from typing import Dict

DB_PATH = "races.db"

EMA_ALPHA = 0.3        # 최근 가중치
WINDOW_LIMIT = 50      # 조회 상한


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_recent_roi_factor(strategy: str) -> float:
    """
    전략별 최근 ROI를 EMA로 요약하여 factor로 반환
    기본값 1.0 (중립)
    """
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT roi
        FROM predictions
        WHERE strategy = ?
          AND roi IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (strategy, WINDOW_LIMIT),
    ).fetchall()
    conn.close()

    if not rows:
        return 1.0

    ema = float(rows[0]["roi"])
    for r in rows[1:]:
        ema = EMA_ALPHA * float(r["roi"]) + (1 - EMA_ALPHA) * ema

    # 과도한 증폭 방지
    return max(0.8, min(1.2, round(ema, 4)))
