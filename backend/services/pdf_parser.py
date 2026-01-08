import pdfplumber
import pandas as pd
import re

def parse_today_pdf(pdf_path: str) -> pd.DataFrame:
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            current_race = None
            for line in text.splitlines():
                # 경주 번호 감지 (예: "서울 1경주")
                m_race = re.search(r'(\d+)경주', line)
                if m_race:
                    current_race = int(m_race.group(1))
                    continue

                # 출전마 라인 (번호 + 말명 + 중량 패턴)
                m = re.match(
                    r'^\s*(\d+)\s+([가-힣A-Za-z]+)\s+.*?\s+(\d+\.\d)',
                    line
                )
                if m and current_race:
                    rows.append({
                        "race_no": current_race,
                        "horse_no": int(m.group(1)),
                        "horse_name": m.group(2),
                        "weight": float(m.group(3))
                    })

    return pd.DataFrame(rows)
