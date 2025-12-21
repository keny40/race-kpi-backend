import csv
import sqlite3

DB_PATH = "races.db"
CSV_PATH = "dummy_races.csv"

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rc_date = row["rc_date"]
            meet = int(row["meet"])
            rc_no = int(row["rc_no"])
            horse_no = int(row["horse_no"])
            rank = int(row["rank"])
            win_odds = float(row["win_odds"])

            race_id = f"{rc_date}_{meet}_{rc_no}"

            cur.execute(
                "INSERT OR IGNORE INTO races VALUES (?,?,?,?)",
                (race_id, rc_date, meet, rc_no)
            )
            cur.execute(
                "INSERT INTO entries (race_id, horse_no, win_odds, rank) VALUES (?,?,?,?)",
                (race_id, horse_no, win_odds, rank)
            )

    con.commit()
    con.close()
    print("CSV data loaded")

if __name__ == "__main__":
    main()
