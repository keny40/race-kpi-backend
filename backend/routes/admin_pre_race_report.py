from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv
import io
import json

from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race"])


def _get_columns(conn):
    cur = conn.execute("PRAGMA table_info(pre_race_run_history)")
    return [r["name"] for r in cur.fetchall()]


@router.get("/report/csv")
def download_csv():
    conn = get_conn()

    cols = _get_columns(conn)

    # 존재하는 컬럼만 선택
    select_cols = ["race_id", "ran_at"]
    optional = ["confidence", "decision", "bet_pass", "hit_miss", "rule_snapshot"]

    for c in optional:
        if c in cols:
            select_cols.append(c)

    sql = f"""
        SELECT {", ".join(select_cols)}
        FROM pre_race_run_history
        ORDER BY ran_at DESC
        LIMIT 500
    """

    cur = conn.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV 헤더는 항상 고정
    writer.writerow([
        "race_id",
        "run_at",
        "confidence",
        "confidence_bucket",
        "decision",
        "bet_pass",
        "hit_miss",
        "rule_snapshot",
    ])

    for r in rows:
        confidence = r.get("confidence")

        # confidence_bucket 계산 (Python)
        if isinstance(confidence, (int, float)):
            if confidence >= 0.7:
                bucket = "HIGH"
            elif confidence >= 0.4:
                bucket = "MID"
            else:
                bucket = "LOW"
        else:
            bucket = ""

        writer.writerow([
            r.get("race_id", ""),
            r.get("ran_at", ""),
            confidence if confidence is not None else "",
            bucket,
            r.get("decision", ""),
            r.get("bet_pass", ""),
            r.get("hit_miss", ""),
            json.dumps(r.get("rule_snapshot"), ensure_ascii=False)
            if isinstance(r.get("rule_snapshot"), (dict, list))
            else (r.get("rule_snapshot") or ""),
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=pre_race_report.csv"
        },
    )
