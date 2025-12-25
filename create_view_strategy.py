import sqlite3

con = sqlite3.connect("races.db")
cur = con.cursor()

cur.execute("""
DROP VIEW IF EXISTS v_race_match_strategy
""")

cur.execute("""
CREATE VIEW v_race_match_strategy AS
SELECT
  p.strategy,
  CASE
    WHEN p.excluded_pass = 1 THEN 'PASS'
    WHEN p.predicted_horse_no = a.winner THEN 'HIT'
    ELSE 'MISS'
  END AS result
FROM predictions p
JOIN race_actuals a
  ON p.race_id = a.race_id
""")

con.commit()
con.close()

print("v_race_match_strategy VIEW created")
