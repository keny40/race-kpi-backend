import sqlite3

DB_PATH = "races.db"

def _weight_from_retry(retry_count: int) -> float:
    # 운영 기본값: 지연이 클수록 KPI 반영을 약화
    if retry_count <= 0:
        return 1.0
    if retry_count <= 2:
        return 0.7
    if retry_count <= 4:
        return 0.4
    return 0.0

def calc_kpi(mode: str = "weight", exclude_retry_ge: int = 5):
    """
    mode:
      - "raw": 그냥 outcome 카운트
      - "exclude": retry_count >= exclude_retry_ge 인 경주는 KPI에서 제외
      - "weight": retry_count에 따라 가중치 적용 (기본 추천)
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # predictions 최신 outcome 기준
    cur.execute("""
        SELECT p.race_id, p.outcome
        FROM predictions p
        WHERE p.outcome IS NOT NULL
    """)
    preds = cur.fetchall()

    stats = {"HIT": 0.0, "MISS": 0.0, "PASS": 0.0}
    total_weight = 0.0

    for race_id, outcome in preds:
        cur.execute("""
            SELECT confirmed_retry_count
            FROM ingest_meta
            WHERE race_id=?
        """, (race_id,))
        row = cur.fetchone()
        retry_count = int(row[0]) if row and row[0] is not None else 0

        if mode == "exclude" and retry_count >= exclude_retry_ge:
            continue

        w = 1.0 if mode in ("raw", "exclude") else _weight_from_retry(retry_count)
        if w <= 0:
            continue

        if outcome in stats:
            stats[outcome] += w
            total_weight += w

    hit_rate = (stats["HIT"] / total_weight * 100.0) if total_weight > 0 else 0.0

    con.close()

    return {
        "HIT": round(stats["HIT"], 2),
        "MISS": round(stats["MISS"], 2),
        "PASS": round(stats["PASS"], 2),
        "TOTAL": round(total_weight, 2),
        "HIT_RATE": round(hit_rate, 2),
        "MODE": mode,
    }
