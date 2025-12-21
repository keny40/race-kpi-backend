import sqlite3
import os
from fastapi import APIRouter

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "races.db")


@router.post("/kpi/testdata/inject")
def inject_testdata():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 테스트용 데이터
    rows = [
        ("default", "HIT"),
        ("default", "HIT"),
        ("default", "MISS"),
        ("default", "PASS"),
        ("model_B", "HIT"),
        ("model_B", "MISS"),
        ("model_B", "MISS"),
        ("model_C", "PASS"),
        ("model_C", "PASS"),
    ]

    for model, decision in rows:
        cur.execute("""
            INSERT INTO predictions (model, decision, confidence, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (model, decision, 0.5))

    con.commit()
    con.close()

    return {
        "status": "OK",
        "inserted": len(rows)
    }
