import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = "backend/db/app.db"

CONF_BINS = [
    (0.30, 0.39),
    (0.40, 0.49),
    (0.50, 1.00),
]


# ======================
# DB
# ======================
def _connect():
    return sqlite3.connect(DB_PATH)


# ======================
# 기간 계산 (호환용)
# ======================
def get_period_range(period: str):
    now = datetime.now()

    if period == "month":
        start = now.replace(day=1)
    elif period == "quarter":
        month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=month, day=1)
    else:
        return None, None

    return start.isoformat(), now.isoformat()


# ======================
# RAW KPI ROW FETCH
# ======================
def fetch_kpi_rows(period_start=None, period_end=None):
    con = _connect()
    cur = con.cursor()

    sql = """
    SELECT p.model, p.decision, p.confidence, a.actual
    FROM predictions p
    JOIN actual_results a ON p.race_id = a.race_id
    """
    params = []

    if period_start and period_end:
        sql += " WHERE p.created_at BETWEEN ? AND ?"
        params = [period_start, period_end]

    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return rows


# ======================
# KPI CORE LOGIC
# ======================
def compute_kpi_rows(rows):
    result = defaultdict(lambda: {
        "total": 0,
        "hit": 0,
        "miss": 0,
        "pass": 0,
        "confidence_bins": defaultdict(lambda: {"hit": 0, "miss": 0})
    })

    for model, decision, confidence, actual in rows:
        r = result[model]
        r["total"] += 1

        if decision == "PASS":
            r["pass"] += 1
            continue

        if decision == actual:
            r["hit"] += 1
            outcome = "hit"
        else:
            r["miss"] += 1
            outcome = "miss"

        for lo, hi in CONF_BINS:
            if lo <= confidence <= hi:
                key = f"{lo:.2f}-{hi:.2f}" if hi < 1 else "0.50+"
                r["confidence_bins"][key][outcome] += 1
                break

    final = {}
    for model, r in result.items():
        denom = r["hit"] + r["miss"]
        accuracy = round(r["hit"] / denom, 4) if denom else 0.0
        pass_rate = round(r["pass"] / r["total"], 4) if r["total"] else 0.0

        final[model] = {
            "model": model,
            "total": r["total"],
            "hit": r["hit"],
            "miss": r["miss"],
            "pass": r["pass"],
            "accuracy": accuracy,
            "pass_rate": pass_rate,
            "confidence_bins": r["confidence_bins"],
        }

    return final


# ======================
# KPI MATRIX (호환용)
# ======================
def fetch_kpi_matrix(period=None):
    start, end = get_period_range(period) if period else (None, None)
    rows = fetch_kpi_rows(start, end)
    data = compute_kpi_rows(rows)

    matrix = []
    for model, r in data.items():
        for bin_key, v in r["confidence_bins"].items():
            matrix.append({
                "model": model,
                "confidence_bin": bin_key,
                "hit": v["hit"],
                "miss": v["miss"]
            })

    return matrix
def prev_period(period: str):
    """
    이전 기간 범위 계산 (kpi_trend 호환용)
    """
    now = datetime.now()

    if period == "month":
        this_start = now.replace(day=1)
        prev_end = this_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)

    elif period == "quarter":
        current_q = (now.month - 1) // 3
        prev_q_end_month = current_q * 3
        if prev_q_end_month <= 0:
            prev_q_end_month = 12
            year = now.year - 1
        else:
            year = now.year

        prev_end = datetime(year, prev_q_end_month, 1) - timedelta(days=1)
        prev_start = datetime(
            prev_end.year,
            ((prev_end.month - 1) // 3) * 3 + 1,
            1
        )
    else:
        return None, None

    return prev_start.isoformat(), prev_end.isoformat()
def record_prediction(
    race_id: str,
    model: str,
    decision: str,
    confidence: float
):
    """
    예측 결과 저장 (predict 라우터 호환용)
    """
    con = _connect()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO predictions (race_id, model, decision, confidence, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            race_id,
            model,
            decision,
            confidence,
            datetime.now().isoformat()
        )
    )

    con.commit()
    con.close()

def upsert_actual_result(
    race_id: str,
    actual: str
):
    """
    실측 결과 저장 또는 업데이트
    """
    con = _connect()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO actual_results (race_id, actual, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(race_id)
        DO UPDATE SET actual=excluded.actual
        """,
        (
            race_id,
            actual,
            datetime.now().isoformat()
        )
    )

    con.commit()
    con.close()


def get_actual_result(race_id: str):
    """
    실측 결과 조회
    """
    con = _connect()
    cur = con.cursor()

    cur.execute(
        """
        SELECT race_id, actual
        FROM actual_results
        WHERE race_id = ?
        """,
        (race_id,)
    )

    row = cur.fetchone()
    con.close()

    if not row:
        return None

    return {
        "race_id": row[0],
        "actual": row[1]
    }
