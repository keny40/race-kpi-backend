import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def _log(msg: str):
    print(f"[KRA_HTML] {datetime.utcnow().isoformat()} {msg}")

def fetch_race_list(date: str) -> List[Dict]:
    """
    date: YYYYMMDD
    return: [{race_id, horses:[{no,name}]}]
    """
    url = f"https://race.kra.co.kr/dbdata/program/raceinfo.do?meet=1&rcDate={date}"
    _log(f"fetch start date={date}")

    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    races: List[Dict] = []

    # 1차 시도: table 기반
    tables = soup.select("table")
    _log(f"found tables={len(tables)}")

    for idx, tb in enumerate(tables):
        horses = _parse_table(tb)
        if horses:
            races.append({
                "race_id": f"{date}-R{idx+1}",
                "horses": horses
            })

    # fallback: 다른 구조 대비
    if not races:
        _log("table parse failed, try fallback selector")
        races = _fallback_parse(soup, date)

    _log(f"parsed races={len(races)}")
    return races


def _parse_table(tb) -> List[Dict]:
    horses = []
    rows = tb.select("tr")
    for r in rows[1:]:
        tds = r.select("td")
        if len(tds) >= 2:
            no = tds[0].get_text(strip=True)
            name = tds[1].get_text(strip=True)
            if no and name:
                horses.append({"no": no, "name": name})
    return horses


def _fallback_parse(soup, date: str) -> List[Dict]:
    races = []
    blocks = soup.select("div, section")
    for idx, b in enumerate(blocks):
        text = b.get_text(" ", strip=True)
        if "마번" in text and "마명" in text:
            horses = []
            spans = b.select("span")
            for s in spans:
                t = s.get_text(strip=True)
                if t:
                    horses.append({"no": "?", "name": t})
            if horses:
                races.append({
                    "race_id": f"{date}-FB{idx+1}",
                    "horses": horses
                })
    return races
