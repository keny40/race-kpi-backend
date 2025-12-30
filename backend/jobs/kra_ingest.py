import os
import requests
import sqlite3

DB_PATH = "races.db"
API_KEY = os.getenv("KRA_API_KEY")

API101 = "https://apis.data.go.kr/B551015/API101_1"  # 경주일/경주번호
API102 = "https://apis.data.go.kr/B551015/API102_1"  # 출전마
API103 = "https://apis.data.go.kr/B551015/API103_1"  # 배당률


def fetch(url, params):
    params["serviceKey"] = API_KEY
    params["numOfRows"] = 100
    params["pageNo"] = 1
    params["resultType"] = "json"

    r = requests.get(url, params=params, timeout=10)

    if r.status_code == 500:
        return []

    r.raise_for_status()
    body = r.json().get("response", {}).get("body", {})
    items = body.get("items", {})
    return items.get("item", []) if items else []


def ingest(date: str, meet_cd: str = "1"):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1️⃣ API101: 경주 목록
    races = fetch(API101, {
        "meetCd": meet_cd,   # 🔴 핵심 수정 포인트
        "rcDate": date
    })

    if not races:
        print(f"[INFO] No race data for {date} (meetCd={meet_cd})")
        return

    for r in races:
        rc_no = int(r["rcNo"])
        race_id = f"{date}-{meet_cd}-{rc_no}"

        cur.execute("""
            INSERT OR IGNORE INTO races
            (race_id, rc_date, rc_no, track)
            VALUES (?, ?, ?, ?)
        """, (race_id, date, rc_no, meet_cd))

        # 2️⃣ API102: 출전마
        entries = fetch(API102, {
            "meetCd": meet_cd,
            "rcDate": date,
            "rcNo": rc_no
        })

        # 3️⃣ API103: 배당률
        odds = fetch(API103, {
            "meetCd": meet_cd,
            "rcDate": date,
            "rcNo": rc_no
        })

        odds_map = {
            int(o["hrNo"]): float(o.get("winOdds", 0))
            for o in odds
        }

        for e in entries:
            horse_no = int(e["hrNo"])
            cur.execute("""
                INSERT OR REPLACE INTO entries
                (race_id, horse_no, horse_name, win_odds)
                VALUES (?, ?, ?, ?)
            """, (
                race_id,
                horse_no,
                e.get("hrName", ""),
                odds_map.get(horse_no, 0)
            ))

    con.commit()
    con.close()
    print(f"[OK] Ingest completed for {date} (meetCd={meet_cd})")


if __name__ == "__main__":
    # 🔴 반드시 실제 경주일
    ingest("20241229", meet_cd="3")  # 부산경남
    ingest("20241229", meet_cd="2")  # 제주

