from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# DB 초기화
# ---------------------------
def init_db():
    conn = sqlite3.connect("races.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS races (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_date TEXT,
            race_no TEXT,
            title TEXT,
            horses TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------------------
# 1) 오늘의 경주 스크래핑
# ---------------------------
@app.get("/scrape/today")
def scrape_today():
    today = datetime.now().strftime("%Y%m%d")
    url = f"http://race.kra.co.kr/raceScore/scoretableScoreScore.do?meet=1&realRcDate={today}"

    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        race_boxes = soup.select(".race_score_tbl")

        if not race_boxes:
            return {"status": "fail", "message": "오늘 경주 정보를 찾을 수 없습니다"}

        conn = sqlite3.connect("races.db")
        cur = conn.cursor()

        for box in race_boxes:
            title = box.select_one(".tit").get_text(strip=True)
            race_no = title.split("경주")[0].replace("제", "").strip()

            horses = []
            rows = box.select("tbody tr")
            for tr in rows:
                cols = [td.get_text(strip=True) for td in tr.select("td")]
                if len(cols) >= 3:
                    horses.append({
                        "순위": cols[0],
                        "마번": cols[1],
                        "마명": cols[2],
                    })

            cur.execute("""
                INSERT INTO races (race_date, race_no, title, horses, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (today, race_no, title, str(horses)))

        conn.commit()
        conn.close()

        return {"status": "ok", "message": "오늘의 경주 스크래핑 완료"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# 2) DB → 경주 목록 조회
# ---------------------------
@app.get("/races")
def get_races():
    conn = sqlite3.connect("races.db")
    cur = conn.cursor()
    cur.execute("SELECT race_date, race_no, title, horses FROM races ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "race_date": row[0],
            "race_no": row[1],
            "title": row[2],
            "horses": row[3],
        })
    return result
