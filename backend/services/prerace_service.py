from backend.services.db import get_conn


def get_prerace_summary(race_id: str):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute(
        """
        SELECT
            race_id,
            finished_at
        FROM pre_race_runs
        WHERE race_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (race_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return {
            "found": False,
            "race_id": race_id,
            "pre_race_run": False,
            "summary": None,
        }

    return {
        "found": True,
        "race_id": row["race_id"],
        "pre_race_run": row["finished_at"] is not None,
        "summary": None,  # ← 아직 요약 저장 구조 없음
    }
