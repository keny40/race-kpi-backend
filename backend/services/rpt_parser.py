import re
import pandas as pd
from pathlib import Path

RACE_HEADER_RE = re.compile(r"제목\s*:\s*(\d{2}\.\d{2}\.\d{2}).*?(\d+)경주")
ENTRY_RE = re.compile(
    r"^\s*(\d+)\s+([가-힣A-Za-z]+)\s+"
    r"(한|미|일|영|호|프)\s+"
    r"(암|수|거)\s+(\d+)\s+([\d\.]+)\s+"
    r"([가-힣]+)\s+([가-힣]+)\s+([가-힣]+)",
    re.MULTILINE
)

def parse_rpt_entries(path: str) -> pd.DataFrame:
    text = Path(path).read_text(encoding="euc-kr", errors="ignore")

    rows = []
    races = list(RACE_HEADER_RE.finditer(text))

    for i, race in enumerate(races):
        race_date = race.group(1)
        race_no = int(race.group(2))

        start = race.end()
        end = races[i + 1].start() if i + 1 < len(races) else len(text)
        block = text[start:end]

        for m in ENTRY_RE.finditer(block):
            rows.append({
                "race_date": race_date,
                "race_no": race_no,
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

    return pd.DataFrame(rows)
