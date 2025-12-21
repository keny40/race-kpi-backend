# backend/utils/race_entries.py

from __future__ import annotations

import csv
from pathlib import Path
from typing import List


CSV_PATH = Path("data") / "races_history.csv"


class RaceDataNotFound(Exception):
    """race_id는 있는데 말 번호가 없거나, CSV가 없는 경우"""


def load_horses_for_race(race_id: str) -> List[int]:
    """
    data/races_history.csv 에서 주어진 race_id의 말 번호 목록을 읽어옵니다.

    CSV 예시는 다음과 같은 컬럼 구조를 가정합니다.
    - race_id : 경주 ID
    - horse_no : 말 번호

    한 race_id에 여러 행이 있을 때 horse_no를 모아서 정렬해서 반환합니다.
    """
    if not CSV_PATH.exists():
        raise RaceDataNotFound(f"CSV 파일이 없습니다: {CSV_PATH}")

    horses = set()

    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("race_id") != race_id:
                continue

            horse_val = row.get("horse_no")
            if horse_val is None:
                continue
            try:
                horses.add(int(horse_val))
            except ValueError:
                # 숫자로 변환 안 되면 스킵
                continue

    if not horses:
        raise RaceDataNotFound(f"race_id={race_id} 에 대한 말 번호를 찾지 못했습니다.")

    return sorted(horses)
