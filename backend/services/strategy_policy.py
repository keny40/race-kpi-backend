import sqlite3
from datetime import datetime

DB_PATH = "races.db"

# 기본 정책(환경변수로 튜닝 가능)
WINDOW = int(__import__("os").getenv("STRATEGY_WINDOW", "80"))
DROP_THRESHOLD = float(__import__("os").getenv("STRATEGY_DROP_THRESHOLD", "12.0"))  # %p 하락
MIN_TOTAL = int(__import__("os").getenv("STRATEGY_MIN_TOTAL", "40"))               # 최소 표본
SOFT_FLOOR = float(__import__("os").getenv("STRATEGY_SOFT_FLOOR", "0.4"))         # 최소 가중치
RECOVER_BOOST = float(__import__("os").getenv("STRATEGY_RECOVER_BOOST", "0.1"))   # 회복 시 가중치 +0.1

def _hit_rate(outcomes):
    if not outcomes:
        return None
    hit = sum(1 for o in outcomes if o == "HIT")
    total = len(outcomes)
    return (hit / total) * 100.0

def _ensure_strategy_row(cur, strategy: str):
    now = datetime.now().isoformat()
    cur.execute("""
        INSERT OR IGNORE INTO strategy_state(strategy, enabled, weight_multiplier, last_score, last_updated_at)
        VALUES (?, 1, 1.0, 0.0, ?)
    """, (strategy, now))

def evaluate_strategy_states():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 전략 목록
    cur.execute("""
        SELECT DISTINCT COALESCE(strategy, 'UNKNOWN')
        FROM predictions
        WHERE outcome IS NOT NULL
    """)
    strategies = [r[0] for r in cur.fetchall()]

    now = datetime.now().isoformat()

    for s in strategies:
        s = s or "UNKNOWN"
        _ensure_strategy_row(cur, s)

        # 최근 2윈도우 outcome 로드(confirmed만)
        cur.execute("""
            SELECT p.outcome
            FROM predictions p
            JOIN ingest_meta m ON p.race_id = m.race_id
            WHERE p.outcome IS NOT NULL
              AND COALESCE(p.strategy, 'UNKNOWN') = ?
              AND m.confirmed_at IS NOT NULL
            ORDER BY m.confirmed_at DESC
            LIMIT ?
        """, (s, WINDOW * 2))
        outs = [x[0] for x in cur.fetchall()]

        if len(outs) < MIN_TOTAL:
            continue

        recent = outs[:WINDOW]
        prev = outs[WINDOW:WINDOW*2]

        r1 = _hit_rate(recent)
        r0 = _hit_rate(prev) if len(prev) >= MIN_TOTAL else None
        if r1 is None or r0 is None:
            continue

        drop = r0 - r1  # 양수면 악화

        cur.execute("SELECT enabled, weight_multiplier FROM strategy_state WHERE strategy=?", (s,))
        enabled, mul = cur.fetchone()
        enabled = int(enabled)
        mul = float(mul)

        # 악화: 가중치 축소 → 심각하면 OFF
        if drop >= DROP_THRESHOLD:
            new_mul = max(SOFT_FLOOR, round(mul - 0.2, 2))
            # 이미 바닥인데도 계속 악화면 OFF
            if new_mul <= SOFT_FLOOR and enabled == 1 and drop >= (DROP_THRESHOLD * 1.5):
                cur.execute("""
                    UPDATE strategy_state
                    SET enabled=0, weight_multiplier=?, last_score=?, last_updated_at=?
                    WHERE strategy=?
                """, (new_mul, round(r1, 2), now, s))
            else:
                cur.execute("""
                    UPDATE strategy_state
                    SET weight_multiplier=?, last_score=?, last_updated_at=?
                    WHERE strategy=?
                """, (new_mul, round(r1, 2), now, s))

        # 회복: ON + 가중치 완만 복구
        else:
            new_mul = min(1.0, round(mul + RECOVER_BOOST, 2))
            new_enabled = 1
            cur.execute("""
                UPDATE strategy_state
                SET enabled=?, weight_multiplier=?, last_score=?, last_updated_at=?
                WHERE strategy=?
            """, (new_enabled, new_mul, round(r1, 2), now, s))

    con.commit()
    con.close()


def get_strategy_state():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT strategy, enabled, weight_multiplier, last_score, last_updated_at
        FROM strategy_state
        ORDER BY strategy ASC
    """)
    rows = cur.fetchall()
    con.close()

    return [
        {
            "strategy": r[0],
            "enabled": int(r[1]),
            "weight_multiplier": float(r[2]),
            "last_hit_rate": float(r[3]),
            "updated_at": r[4],
        }
        for r in rows
    ]
