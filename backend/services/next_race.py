import sqlite3
from datetime import datetime
from backend.services.db import DB_PATH


def ensure_next_race():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 이미 있으면 그대로 사용
    row = cur.execute(
        """
        SELECT race_id, rc_date, rc_no, distance, grade, status
        FROM races
        ORDER BY rc_date DESC, rc_no DESC
        LIMIT 1
        """
    ).fetchone()

    if row:
        conn.close()
        return {
            "race_id": row[0],
            "rc_date": row[1],
            "rc_no": row[2],
            "distance": row[3],
            "grade": row[4],
            "status": row[5],
        }

    # 없으면 MVP용 더미 생성
    today = datetime.now().strftime("%Y%m%d")
    race = {
        "race_id": f"{today}_NEXT",
        "rc_date": today,
        "rc_no": 1,
        "distance": 1200,
        "grade": "MVP",
        "status": "READY",
    }

    cur.execute(
        """
        INSERT OR REPLACE INTO races
        (race_id, rc_date, rc_no, distance, grade, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            race["race_id"],
            race["rc_date"],
            race["rc_no"],
            race["distance"],
            race["grade"],
            race["status"],
        ),
    )

    conn.commit()
    conn.close()
    return race
