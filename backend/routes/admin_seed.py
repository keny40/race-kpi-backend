from fastapi import APIRouter, Request, HTTPException
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])
ADMIN_PASSWORD = "admin123"
DB_PATH = "backend/races.db"


def _auth(request: Request):
    if request.headers.get("x-admin-token") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


def _ensure_columns(cur):
    """
    races 테이블에 필요한 컬럼이 없으면 추가
    (SQLite는 ADD COLUMN만 가능)
    """
    cur.execute("PRAGMA table_info(races)")
    existing = {row[1] for row in cur.fetchall()}

    columns = {
        "meet": "TEXT",
        "track": "TEXT",
        "rc_no": "INTEGER",
        "start_time": "TEXT",
        "status": "TEXT",
        "distance_m": "INTEGER",
        "runners": "INTEGER",
    }

    for col, col_type in columns.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE races ADD COLUMN {col} {col_type}")


@router.post("/seed-next-race")
def seed_next_race(request: Request):
    _auth(request)

    race_date = datetime.now().strftime("%Y%m%d")
    race_id = f"{race_date}_SEO_01"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 테이블 최소 보장
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS races (
            race_id TEXT PRIMARY KEY
        )
        """
    )

    # 🔑 컬럼 자동 보정
    _ensure_columns(cur)

    # 안전한 INSERT
    cur.execute(
        """
        INSERT OR REPLACE INTO races
        (race_id, meet, track, rc_no, start_time, status, distance_m, runners)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            race_id,
            "SEO",
            "서울",
            1,
            "12:00",
            "SCHEDULED",
            1200,
            10,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "race_id": race_id
    }
