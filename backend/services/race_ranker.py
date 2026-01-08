# backend/services/race_ranker.py
import os
import sqlite3
from typing import List, Dict, Any

def _db():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "races.db")

def get_race_rankings(race_id: str) -> Dict[int, List[Dict[str, Any]]]:
    """
    race_id 기준
    → {경주번호: [말별 AI 랭킹]}
    """
    conn = sqlite3.connect(_db())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT
        e.race_no,
        e.horse_no,
        e.horse_name,
        s.score,
        s.r_norm,
        s.win_rate,
        s.quinella_rate
    FROM race_entries e
    LEFT JOIN horse_scores s
      ON e.horse_name = s.horse_name
    WHERE e.race_id = ?
    ORDER BY e.race_no, s.score DESC
    """, (race_id,)).fetchall()

    conn.close()

    out: Dict[int, List[Dict[str, Any]]] = {}
    for r in rows:
        race_no = r["race_no"]
        out.setdefault(race_no, []).append({
            "horse_no": r["horse_no"],
            "horse_name": r["horse_name"],
            "score": r["score"] or 0.0,
            "r_norm": r["r_norm"],
            "win_rate": r["win_rate"],
            "quinella_rate": r["quinella_rate"],
        })

    # 랭킹 부여
    for race_no, items in out.items():
        items.sort(key=lambda x: x["score"], reverse=True)
        for i, it in enumerate(items, start=1):
            it["rank"] = i

    return out
