# backend/services/strategy_weights.py
import sqlite3

DB_PATH = "races.db"


def get_weight(strategy: str) -> float:
    """
    전략별 가중치 조회
    없으면 기본값 1.0
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT weight FROM strategy_weights WHERE strategy=?",
        (strategy,)
    ).fetchone()
    conn.close()
    return float(row[0]) if row else 1.0


def apply_weight(score: float, strategy: str) -> float:
    """
    점수 × 전략 가중치
    """
    return score * get_weight(strategy)
