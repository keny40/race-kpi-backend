# backend/predict_store.py
import sqlite3


def store_prediction(db_path, race_id, result):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        cur.execute("""
            INSERT INTO predictions
            (race_id, horse_label, confidence, gap, action)
            VALUES (?, ?, ?, ?, ?)
        """, (
            race_id,
            result["label"],
            result["confidence"],
            result["meta"]["gap"],
            result["meta"]["action"],
        ))

        con.commit()
        con.close()
    except Exception:
        pass
