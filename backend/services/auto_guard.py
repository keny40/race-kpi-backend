from backend.services.db import get_conn


def evaluate_and_apply_guard():
    conn = get_conn()
    cur = conn.cursor()

    cfg = cur.execute(
        "SELECT * FROM guard_config WHERE id = 1"
    ).fetchone()

    if not cfg:
        return {
            "forced": 0,
            "avg_ev": None,
            "hit_rate": None,
            "consec_miss": None,
            "reason": "no_guard_config",
        }

    rows = cur.execute(
        """
        SELECT hit_miss, live_ev
        FROM pre_race_run_history
        WHERE hit_miss IS NOT NULL
        ORDER BY run_at DESC
        LIMIT ?
        """,
        (cfg["window_size"],),
    ).fetchall()

    if not rows:
        return {
            "forced": 0,
            "avg_ev": None,
            "hit_rate": None,
            "consec_miss": None,
            "reason": "no_history",
        }

    total = len(rows)
    hits = sum(1 for r in rows if r["hit_miss"] == "HIT")
    hit_rate = hits / total

    avg_ev = sum(r["live_ev"] for r in rows) / total

    consec_miss = 0
    for r in rows:
        if r["hit_miss"] == "MISS":
            consec_miss += 1
        else:
            break

    forced = 0
    reason = "ok"

    if hit_rate < cfg["min_hit_rate"]:
        forced = 1
        reason = "hit_rate_low"
    elif avg_ev < cfg["immediate_ev_threshold"]:
        forced = 1
        reason = "avg_ev_low"
    elif consec_miss >= cfg["consec_miss_limit"]:
        forced = 1
        reason = "consec_miss"

    return {
        "forced": forced,
        "avg_ev": round(avg_ev, 4),
        "hit_rate": round(hit_rate, 4),
        "consec_miss": consec_miss,
        "reason": reason,
    }


# ✅ 강제 중단
def force_stop_guard():
    conn = get_conn()
    conn.execute(
        "UPDATE guard_config SET immediate_ev_threshold = -999 WHERE id = 1"
    )
    conn.commit()


# ✅ 중단 해제 (초기값으로 복원)
def release_guard():
    conn = get_conn()
    conn.execute(
        "UPDATE guard_config SET immediate_ev_threshold = -0.1 WHERE id = 1"
    )
    conn.commit()
