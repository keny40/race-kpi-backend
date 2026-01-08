import re
import json
from pathlib import Path
import pandas as pd

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).resolve().parent
RPT_PATH = BASE_DIR / "20260103dacom01.rpt"

OUT_DIR = BASE_DIR / "parsed_output"
OUT_DIR.mkdir(exist_ok=True)

# =========================
# Robust reader
# =========================
def read_lines(path: Path):
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return raw.decode(enc).splitlines(), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace").splitlines(), "utf-8(errors=replace)"

# =========================
# Parser (fixed for Dacom RPT)
# =========================
def parse_rpt(path: Path):
    lines, enc = read_lines(path)

    races = []
    horses = []

    current_race = None
    race_date = None
    race_no = None

    for raw in lines:
        line = raw.rstrip()

        # ---------------------------------
        # 1) 경주 제목 라인
        # 예: 제목 : 26.01.03 제 1 일 토 요일 1경주;
        # ---------------------------------
        m = re.search(r"제목\s*:\s*(\d{2}\.\d{2}\.\d{2}).*?(\d+)경주", line)
        if m:
            date_raw = m.group(1)   # 26.01.03
            race_no = int(m.group(2))

            yy, mm, dd = date_raw.split(".")
            race_date = f"20{yy}-{mm}-{dd}"

            race_id = f"{race_date.replace('-', '')}_{race_no:02d}"

            current_race = {
                "race_id": race_id,
                "race_date": race_date,
                "track": "서울",
                "race_no": race_no,
                "distance": None,
                "grade": None,
                "start_time": None,
            }
            races.append(current_race)
            continue

        if not current_race:
            continue

        # ---------------------------------
        # 2) 거리 / 등급 / 출발시각
        # 예: 1200 M 출전:9두 국6등급 (R0~0 3세 ) 출발:10:35
        # ---------------------------------
        m = re.search(
            r"(\d+)\s*M.*?(국\d+등급).*?출발[:：](\d{2}:\d{2})",
            line
        )
        if m:
            current_race["distance"] = int(m.group(1))
            current_race["grade"] = m.group(2).replace("등급", "")
            current_race["start_time"] = m.group(3)
            continue

        # ---------------------------------
        # 3) 출전마 라인
        # 예:
        # 1  컴퍼스포스    한 암 3 54.5   정우주   임채덕   이상진
        # ---------------------------------
        m = re.match(
            r"^\s*(\d+)\s+([가-힣A-Za-z0-9]+)\s+"
            r"([한외])\s+([암수거])\s+"
            r"(\d+)\s+([\d\.]+)\s+"
            r"([가-힣A-Za-z0-9]+)\s+"
            r"([가-힣A-Za-z0-9]+)\s+"
            r"([가-힣A-Za-z0-9]+)",
            line
        )
        if m:
            horses.append({
                "race_id": current_race["race_id"],
                "horse_no": int(m.group(1)),
                "horse_name": m.group(2),
                "origin": m.group(3),
                "sex": m.group(4),
                "age": int(m.group(5)),
                "weight": float(m.group(6)),
                "jockey": m.group(7),
                "trainer": m.group(8),
                "owner": m.group(9),
            })
            continue

    return pd.DataFrame(races), pd.DataFrame(horses), enc

# =========================
# Main
# =========================
def main():
    if not RPT_PATH.exists():
        raise FileNotFoundError(RPT_PATH)

    df_races, df_horses, enc = parse_rpt(RPT_PATH)

    df_races.to_csv(OUT_DIR / "races.csv", index=False, encoding="utf-8-sig")
    df_horses.to_csv(OUT_DIR / "horses.csv", index=False, encoding="utf-8-sig")

    races_json = []
    for _, r in df_races.iterrows():
        rid = r["race_id"]
        horses = df_horses[df_horses["race_id"] == rid]
        races_json.append({
            "race_id": rid,
            "meta": r.to_dict(),
            "horses": horses.to_dict(orient="records")
        })

    with open(OUT_DIR / "races.json", "w", encoding="utf-8") as f:
        json.dump(races_json, f, ensure_ascii=False, indent=2)

    print("✅ 파싱 완료")
    print(f"- encoding: {enc}")
    print(f"- races: {len(df_races)}")
    print(f"- horses: {len(df_horses)}")
    print(f"- output: {OUT_DIR}")

if __name__ == "__main__":
    main()
