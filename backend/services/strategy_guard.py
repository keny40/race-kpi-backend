# backend/services/strategy_guard.py
import sqlite3
from backend.services.alert_slack import send
from backend.services.strategy_state import set_strategy_enabled

DB_PATH = "races.db"
HIT_KILL = 0.30
ROI_KILL = 0.90
WINDOW = 80

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def evaluate_and_kill():
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT p.strategy,
               AVG(CASE WHEN p.decision = a.winner THEN 1.0 ELSE 0.0 END) AS hit_rate,
               AVG(COALESCE(p.roi,1.0)) AS avg_roi,
               COUNT(*) AS cnt
        FROM predictions p
        JOIN actual_results a ON p.race_id = a.race_id
        GROUP BY p.strategy
        HAVING cnt >= ?
    """, (WINDOW,)).fetchall()
    conn.close()

    for r in rows:
        if r["hit_rate"] < HIT_KILL or r["avg_roi"] < ROI_KILL:
            set_strategy_enabled(r["strategy"], False)
            send(
                f"⛔ *AUTO KILL* `{r['strategy']}`\n"
                f"hit={r['hit_rate']:.3f} roi={r['avg_roi']:.3f}",
                blocks=[
                    {"type":"section","text":{"type":"mrkdwn",
                     "text":f"*AUTO KILL* `{r['strategy']}`\n"
                             f"hit={r['hit_rate']:.3f} roi={r['avg_roi']:.3f}"}},
                    {"type":"actions","elements":[
                        {"type":"button","text":{"type":"plain_text","text":"RE-ENABLE"},
                         "style":"primary","value":r["strategy"]}
                    ]}
                ]
            )
