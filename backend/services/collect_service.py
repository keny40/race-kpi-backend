from typing import Dict, Any
from fastapi import UploadFile
import csv
import io
import sqlite3
import json
from datetime import datetime

DB_PATH = "backend/races.db"


def _generate_pre_race_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    MVP용 pre-race 요약 생성
    (향후 실제 예측 로직으로 교체 예정)
    """
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "race_date": row.get("race_date") or row.get("경주일자"),
        "meet": row.get("meet") or row.get("경마장"),
        "race_no": row.get("race_no") or row.get("경주번호"),
        "confidence": round(0.6 + (hash(row.get("race_no")) % 30) / 100, 2),
        "note": "MVP pre-race summary",
    }


async def parse_and_insert_upload(
    file: UploadFile,
    trigger_prerace: bool = False,
) -> Dict[str, Any]:
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(text))
    inserted = 0
    skipped = 0
    errors = []

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for idx, row in enumerate(reader, start=1):
        try:
            race_date = row.get("경주일자") or row.get("race_date")
            meet = row.get("경마장") or row.get("meet")
            race_no = row.get("경주번호") or row.get("race_no")
            start_time = row.get("출발시간") or row.get("start_time")
            title = row.get("경주명") or row.get("title")

            if not race_date or not race_no:
                skipped += 1
                continue

            pre_race_summary = None
            pre_race_run = 0

            if trigger_prerace:
                summary = _generate_pre_race_summary(row)
                pre_race_summary = json.dumps(summary, ensure_ascii=False)
                pre_race_run = 1

            cur.execute(
                """
                INSERT OR IGNORE INTO races
                (race_date, meet, race_no, start_time, title, extra_json,
                 pre_race_run, pre_race_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_date,
                    meet,
                    int(race_no),
                    start_time,
                    title,
                    json.dumps(row, ensure_ascii=False),
                    pre_race_run,
                    pre_race_summary,
                ),
            )

            if cur.rowcount:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            errors.append(f"row#{idx}: {str(e)}")

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "meta": {
            "filename": file.filename,
            "trigger_prerace": trigger_prerace,
        },
    }
