import requests
import sqlite3
from xml.etree import ElementTree as ET

SERVICE_KEY = "여기에_본인_인증키"
DB_PATH = "races.db"

def fetch(rc_date: str, meet: int):
    url = "https://apis.data.go.kr/B551015/API299"
    params = {
        "serviceKey": SERVICE_KEY,
        "rc_date": rc_date,
        "meet": meet,
        "_type": "xml"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return ET.fromstring(r.text)

def save(root):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    for item in root.findall(".//item"):
        rc_date = item.findtext("rcDate")
        meet = int(item.findtext("meet"))
        rc_no = int(item.findtext("rcNo"))
        horse_no = int(item.findtext("hrNo"))
        rank = int(item.findtext("ord"))
        odds = float(item.findtext("winOdds", "0") or 0)

        race_id = f"{rc_date}_{meet}_{rc_no}"

        cur.execute(
            "INSERT OR IGNORE INTO races VALUES (?,?,?,?)",
            (race_id, rc_date, meet, rc_no)
        )

        cur.execute(
            "INSERT INTO entries (race_id, horse_no, win_odds, rank) VALUES (?,?,?,?)",
            (race_id, horse_no, odds, rank)
        )

    con.commit()
    con.close()

if __name__ == "__main__":
    root = fetch("20240107", 1)  # 서울, 일요일
    save(root)
    print("API299 data saved")

