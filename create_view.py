import sqlite3

con = sqlite3.connect("races.db")
cur = con.cursor()

cur.executescript("""
DROP VIEW IF EXISTS v_race_match;

CREATE VIEW v_race_match AS
SELECT
  p.id AS prediction_id,
  p.race_id,
  p.predicted_horse_no,
  p.confidence,
  r.winner,
  CASE
    WHEN p.passed = 1 THEN 'PASS'
    WHEN p.predicted_horse_no = r.winner THEN 'HIT'
    ELSE 'MISS'
  END AS result,
  p.created_at
FROM predictions p
JOIN results r
  ON p.race_id = r.race_id;
""")

con.commit()
con.close()

print("v_race_match VIEW recreated (OK)")
