# backend/ops_reporting.py
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Tuple

from .pdf_reports import build_ops_pdf_bytes


def _db_path() -> str:
    env = os.getenv("RACES_DB_PATH")
    if env and os.path.exists(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "races.db")


def _reports_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "reports", "generated")
    os.makedirs(path, exist_ok=True)
    return path


def _period_range(period: str) -> Tuple[str, str, str]:
    now = datetime.now()
    if period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # 다음달 1일 - 1초 (표시용)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        label = f"{start.year:04d}-{start.month:02d}"
        return (start.isoformat(sep=" "), end.isoformat(sep=" "), label)

    if period == "quarterly":
        q = ((now.month - 1) // 3) + 1
        start_month = (q - 1) * 3 + 1
        start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_month == 10:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start_month + 3)
        label = f"{start.year:04d}-Q{q}"
        return (start.isoformat(sep=" "), end.isoformat(sep=" "), label)

    raise ValueError("period must be 'monthly' or 'quarterly'")


def fetch_ops_summary(con: sqlite3.Connection, time_min: str, time_max: str) -> Dict[str, Any]:
    # predictions 테이블이 없으면 0으로 처리
    cur = con.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'
    """)
    if cur.fetchone() is None:
        return {
            "total": 0, "pass": 0, "non_pass": 0,
            "hit": 0, "miss": 0,
            "pass_rate": 0.0, "hit_rate_ex_pass": 0.0,
        }

    # created_at이 없을 수도 있어 안전하게 try
    where = "1=1"
    params = []
    # created_at 컬럼 확인
    cur.execute("PRAGMA table_info(predictions)")
    cols = {r[1] for r in cur.fetchall()}
    if "created_at" in cols:
        where = "created_at >= ? AND created_at < ?"
        params = [time_min, time_max]

    cur.execute(f"""
        SELECT COUNT(*),
               SUM(CASE WHEN label='PASS' THEN 1 ELSE 0 END),
               SUM(CASE WHEN label!='PASS' THEN 1 ELSE 0 END)
        FROM predictions
        WHERE {where}
    """, params)
    total, pass_cnt, non_pass = cur.fetchone()
    pass_cnt = pass_cnt or 0
    non_pass = non_pass or 0

    # HIT/MISS는 feedback(또는 results) 테이블이 있는 경우만 집계
    hit = miss = 0
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('feedback','result_feedback','results')
    """)
    tbl = cur.fetchone()
    if tbl:
        tbl = tbl[0]
        # 기대 컬럼을 유연하게 처리
        cur.execute(f"PRAGMA table_info({tbl})")
        fcols = {r[1] for r in cur.fetchall()}
        if {"is_hit", "created_at"}.issubset(fcols):
            cur.execute(
                f"""
                SELECT
                  SUM(CASE WHEN is_hit=1 THEN 1 ELSE 0 END),
                  SUM(CASE WHEN is_hit=0 THEN 1 ELSE 0 END)
                FROM {tbl}
                WHERE created_at >= ? AND created_at < ?
                """,
                (time_min, time_max),
            )
            row = cur.fetchone()
            hit = (row[0] or 0) if row else 0
            miss = (row[1] or 0) if row else 0

    pass_rate = (pass_cnt / total) if total else 0.0
    hit_rate_ex_pass = (hit / (hit + miss)) if (hit + miss) else 0.0

    return {
        "total": int(total or 0),
        "pass": int(pass_cnt),
        "non_pass": int(non_pass),
        "hit": int(hit),
        "miss": int(miss),
        "pass_rate": round(pass_rate, 4),
        "hit_rate_ex_pass": round(hit_rate_ex_pass, 4),
    }


def build_and_save_report_pdf(period: str) -> str:
    time_min, time_max, label = _period_range(period)

    con = sqlite3.connect(_db_path(), timeout=5.0, check_same_thread=False)
    try:
        summary = fetch_ops_summary(con, time_min, time_max)
    finally:
        con.close()

    pdf_bytes = build_ops_pdf_bytes(
        title=f"OPS Report ({period})",
        period_label=label,
        time_min=time_min,
        time_max=time_max,
        summary=summary,
    )

    outdir = _reports_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ops_{period}_{label}_{ts}.pdf".replace(":", "-")
    outpath = os.path.join(outdir, filename)

    with open(outpath, "wb") as f:
        f.write(pdf_bytes)

    return outpath
