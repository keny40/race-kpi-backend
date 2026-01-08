import sqlite3
from typing import Dict, Any, Optional, Tuple, List
import math

DB_PATH = "races.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _clip(p: float, eps: float = 1e-6) -> float:
    if p < eps:
        return eps
    if p > 1 - eps:
        return 1 - eps
    return p


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def _logit(p: float) -> float:
    p = _clip(p)
    return math.log(p / (1.0 - p))


def ensure_calibration_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS calibration_params (
          strategy TEXT PRIMARY KEY,
          a REAL NOT NULL,
          b REAL NOT NULL,
          n INTEGER NOT NULL,
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def fit_platt(strategy: Optional[str] = None, min_samples: int = 50, iters: int = 400, lr: float = 0.05) -> Dict[str, Any]:
    """
    A,B fit: p_cal = sigmoid(A*logit(conf)+B)
    학습 데이터: predictions JOIN actual_results
    """
    ensure_calibration_table()

    conn = _conn()
    cur = conn.cursor()

    params: List[Any] = []
    where_strategy = ""
    if strategy:
        where_strategy = " AND p.strategy = ? "
        params.append(strategy)

    rows = cur.execute(
        f"""
        SELECT p.strategy, p.confidence, a.winner, p.predicted_horse_no
        FROM predictions p
        JOIN actual_results a ON a.race_id = p.race_id
        WHERE p.passed = 0
          AND p.predicted_horse_no IS NOT NULL
          {where_strategy}
        """,
        params,
    ).fetchall()

    if not rows or len(rows) < min_samples:
        conn.close()
        return {"ok": False, "reason": "not_enough_samples", "n": len(rows) if rows else 0}

    by_strategy: Dict[str, List[Tuple[float, int]]] = {}
    for r in rows:
        s = r["strategy"]
        conf = float(r["confidence"])
        y = 1 if int(r["predicted_horse_no"]) == int(r["winner"]) else 0
        by_strategy.setdefault(s, []).append((conf, y))

    def _fit_one(data: List[Tuple[float, int]]) -> Tuple[float, float]:
        A = 1.0
        B = 0.0
        for _ in range(iters):
            gA = 0.0
            gB = 0.0
            for conf, y in data:
                x = _logit(conf)
                p = _sigmoid(A * x + B)
                gA += (p - y) * x
                gB += (p - y)
            A -= lr * (gA / len(data))
            B -= lr * (gB / len(data))
        return A, B

    updated = []
    for s, data in by_strategy.items():
        A, B = _fit_one(data)
        cur.execute(
            """
            INSERT INTO calibration_params(strategy, a, b, n, updated_at)
            VALUES(?, ?, ?, ?, datetime('now'))
            ON CONFLICT(strategy) DO UPDATE SET
              a=excluded.a, b=excluded.b, n=excluded.n, updated_at=excluded.updated_at
            """,
            (s, float(A), float(B), int(len(data))),
        )
        updated.append({"strategy": s, "a": A, "b": B, "n": len(data)})

    conn.commit()
    conn.close()
    return {"ok": True, "updated": updated}


def load_params(strategy: str) -> Optional[Tuple[float, float]]:
    ensure_calibration_table()
    conn = _conn()
    cur = conn.cursor()
    row = cur.execute("SELECT a, b FROM calibration_params WHERE strategy = ?", (strategy,)).fetchone()
    conn.close()
    if not row:
        return None
    return float(row["a"]), float(row["b"])


def calibrate_confidence(strategy: str, confidence: float) -> float:
    params = load_params(strategy)
    if not params:
        return float(confidence)
    A, B = params
    x = _logit(float(confidence))
    return _sigmoid(A * x + B)


def backfill_calibrated_confidence(strategy: Optional[str] = None, min_confidence: float = 0.0) -> Dict[str, Any]:
    """
    기존 predictions의 calibrated_confidence를 일괄 채움
    """
    ensure_calibration_table()
    conn = _conn()
    cur = conn.cursor()

    params: List[Any] = [float(min_confidence)]
    where_strategy = ""
    if strategy:
        where_strategy = " AND strategy = ? "
        params.append(strategy)

    rows = cur.execute(
        f"""
        SELECT id, strategy, confidence
        FROM predictions
        WHERE passed = 0
          AND predicted_horse_no IS NOT NULL
          AND confidence >= ?
          {where_strategy}
        """,
        params,
    ).fetchall()

    updated = 0
    for r in rows:
        cid = int(r["id"])
        s = r["strategy"]
        conf = float(r["confidence"])
        cal = calibrate_confidence(s, conf)
        cur.execute("UPDATE predictions SET calibrated_confidence = ? WHERE id = ?", (float(cal), cid))
        updated += 1

    conn.commit()
    conn.close()
    return {"ok": True, "updated": updated}
