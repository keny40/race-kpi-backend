# backend/services/race_entry.py
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

def _db():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "races.db")

def init_race_entry_table():
    conn = sqlite3.connect(_db())
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_entries (
        race_id TEXT,
        race_no INTEGER,
        horse_no INTEGER,
        horse_name TEXT,
        PRIMARY KEY (race_id, horse_no)
    )
    """)
    conn.commit()
    conn.close()

def load_race_entries_xlsx(xlsx_path: str, race_id: str):
    """
    엑셀 형식 가정:
    - 경주번호
    - 번호
    - 마명
    """
    init_race_entry_table()
    df = pd.read_excel(xlsx_path)

    required = ["경주번호", "번호", "마명"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"missing column: {c}")

    rows = []
    for _, r in df.iterrows():
        rows.append((
            race_id,
            int(r["경주번호"]),
            int(r["번호"]),
            str(r["마명"]).strip()
        ))

    conn = sqlite3.connect(_db())
    cur = conn.cursor()
    cur.executemany("""
    INSERT OR REPLACE INTO race_entries
    (race_id, race_no, horse_no, horse_name)
    VALUES (?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()

    return {"ok": True, "loaded": len(rows)}
