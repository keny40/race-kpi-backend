# backend/routes/admin_pre_race_kpi.py

@router.get("/kpi")
def get_pre_race_kpi():
    conn = get_conn()

    avg = conn.execute("""
      SELECT AVG(confidence) AS avg_conf
      FROM pre_race_run_history
      ORDER BY run_at DESC
      LIMIT 20
    """).fetchone()["avg_conf"]

    counts = conn.execute("""
      SELECT decision, COUNT(*) c
      FROM pre_race_run_history
      GROUP BY decision
    """).fetchall()

    paused = is_paused()

    return {
      "avg_confidence": round(avg or 0, 3),
      "decision_counts": {r["decision"]: r["c"] for r in counts},
      "paused": paused
    }
