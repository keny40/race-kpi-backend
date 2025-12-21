# backend/offline/data_loader.py

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class RaceRecord:
    race_id: str
    horse_no: int
    is_winner: int  # 1 = 우승, 0 = 나머지


def load_race_csv(csv_path: str) -> List[RaceRecord]:
    """
    CSV 파일에서 경주 기록을 읽어와 RaceRecord 리스트로 변환합니다.

    기본 기대 컬럼:
      race_id, horse_no, is_winner

    예시:
      race_id,horse_no,is_winner
      2025010101,3,1
      2025010101,5,0
      2025010101,7,0
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"경로에 CSV 파일이 없습니다: {csv_path}")

    records: List[RaceRecord] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"race_id", "horse_no", "is_winner"}
        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV에 다음 컬럼이 필요합니다: {missing}")

        for row in reader:
            try:
                race_id = str(row["race_id"]).strip()
                horse_no = int(row["horse_no"])
                is_winner = int(row["is_winner"])
            except Exception as e:
                # 매우 러프하게: 문제가 있는 행은 스킵
                print(f"[WARN] 행 파싱 실패, 건너뜀: {row} / {e}")
                continue

            records.append(RaceRecord(race_id=race_id,
                                      horse_no=horse_no,
                                      is_winner=is_winner))
    return records
