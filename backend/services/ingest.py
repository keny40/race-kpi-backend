import sqlite3
import os
from datetime import datetime

from .kra_api import fetch_all_kra_results
from .performance import update_prediction_performance
from .notify import notify_slack
from .time_policy import is_after_expected_end
from .endtime_estimator import estimate_expected_end_hhmm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "races.db")

MAX_RETRY = 5


def ingest_results():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # =====================================================
    # 1️⃣ 재시도 큐 우선 처리
    # =====================================================
    cur.execute("""
        SELECT id, rc_date, meet, rc_no, retry_count
        FROM retry_queue
        ORDER BY updated_at ASC
    """)
    retry_rows = cur.fetchall()

    for qid, rc_date, meet, rc_no, retry_count in retry_rows:
        try:
            results = fetch_all_kra_results(
                rc_date=rc_date,
                meet=meet,
                rc_no=rc_no
            )

            success = _process_results(
                results,
                cur,
                retry_count_override=retry_count
            )

            if success:
                cur.execute("DELETE FROM retry_queue WHERE id=?", (qid,))
            else:
                _update_retry(cur, qid, retry_count, "미확정/지연")

        except Exception as e:
            _update_retry(cur, qid, retry_count, str(e))

    # =====================================================
    # 2️⃣ 일반 자동 수집
    # =====================================================
    try:
        results = fetch_all_kra_results(
            rc_year=os.getenv("KRA_RC_YEAR"),
            rc_month=os.getenv("KRA_RC_MONTH"),
            rc_date=os.getenv("KRA_RC_DATE"),
            meet=os.getenv("KRA_MEET"),
        )

        _process_results(
            results,
            cur,
            retry_count_override=None
        )

    except Exception as e:
        notify_slack(f"[KRA INGEST FAIL] {e}")

    con.commit()
    con.close()


# -----------------------------------------------------
# 내부 처리 로직
# -----------------------------------------------------

def _process_results(results, cur, retry_count_override: int | None):
    inserted = 0

    for r in results:
        rc_date = r.get("rcDate")
        meet = _to_int(r.get("meet"))
        rc_no = _to_int(r.get("rcNo"))

        if not rc_date or not meet or not rc_no:
            continue

        race_id = f"{rc_date}_{meet}_{rc_no}"

        # ===============================
        # 메타: 최초 관측 기록
        # ===============================
        _meta_upsert_first_seen(cur, race_id, rc_date, meet, rc_no)

        # ===============================
        # 종료 예상시간 결정
        # ===============================
        exp_end = r.get("expEndTime")
        if not exp_end:
            exp_end = estimate_expected_end_hhmm(rc_date, meet, rc_no)

        _meta_update_expected_end(cur, race_id, exp_end)

        # ===============================
        # 종료 후 대기 정책
        # ===============================
        if not is_after_expected_end(rc_date, meet, rc_no, exp_end):
            _enqueue_retry(cur, rc_date, meet, rc_no, "종료 전/대기구간")
            continue

        # ===============================
        # 결과 확정 여부 (ord)
        # ===============================
        if not r.get("ord"):
            _enqueue_retry(cur, rc_date, meet, rc_no, "결과 미확정")
            continue

        winner = r.get("hrNo")
        if not winner:
            _enqueue_retry(cur, rc_date, meet, rc_no, "winner 누락")
            continue

        payoff = float(r.get("winAmt", 0))

        # ===============================
        # 결과 저장
        # ===============================
        cur.execute("""
            INSERT OR IGNORE INTO results (race_id, winner, payoff)
            VALUES (?, ?, ?)
        """, (race_id, winner, payoff))

        if cur.rowcount > 0:
            inserted += 1

            confirmed_retry = _current_retry_count_for(cur, rc_date, meet, rc_no)
            if retry_count_override is not None:
                confirmed_retry = max(
                    confirmed_retry,
                    int(retry_count_override)
                )

            _meta_mark_confirmed(cur, race_id, confirmed_retry)

            update_prediction_performance(race_id)

            # 동일 경주 재시도 큐 잔재 제거
            cur.execute("""
                DELETE FROM retry_queue
                WHERE rc_date=? AND meet=? AND rc_no=?
            """, (rc_date, meet, rc_no))

    if inserted > 0:
        notify_slack(f"[KRA INGEST] 신규 확정 결과 {inserted}건 반영")

    return inserted > 0


# -----------------------------------------------------
# Retry Queue 관리
# -----------------------------------------------------

def _enqueue_retry(cur, rc_date, meet, rc_no, reason):
    cur.execute("""
        SELECT id FROM retry_queue
        WHERE rc_date=? AND meet=? AND rc_no=?
        LIMIT 1
    """, (rc_date, meet, rc_no))
    row = cur.fetchone()

    now = datetime.now().isoformat()

    if row:
        cur.execute("""
            UPDATE retry_queue
            SET last_error=?, updated_at=?
            WHERE rc_date=? AND meet=? AND rc_no=?
        """, (reason, now, rc_date, meet, rc_no))
    else:
        cur.execute("""
            INSERT INTO retry_queue
            (rc_date, meet, rc_no, retry_count, last_error, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (rc_date, meet, rc_no, reason, now))


def _update_retry(cur, qid, retry_count, error):
    now = datetime.now().isoformat()

    if int(retry_count) + 1 >= MAX_RETRY:
        notify_slack(f"[KRA RETRY DROP] id={qid}, error={error}")
        cur.execute("DELETE FROM retry_queue WHERE id=?", (qid,))
        return

    cur.execute("""
        UPDATE retry_queue
        SET retry_count = retry_count + 1,
            last_error = ?,
            updated_at = ?
        WHERE id=?
    """, (error, now, qid))


# -----------------------------------------------------
# ingest_meta 관리
# -----------------------------------------------------

def _weekday_and_season(rc_date: str):
    dt = datetime.strptime(rc_date, "%Y%m%d")
    weekday = dt.weekday()  # 0=Mon
    m = dt.month
    if m in (12, 1, 2):
        season = "WINTER"
    elif m in (3, 4, 5):
        season = "SPRING"
    elif m in (6, 7, 8):
        season = "SUMMER"
    else:
        season = "FALL"
    return weekday, season


def _meta_upsert_first_seen(cur, race_id, rc_date, meet, rc_no):
    weekday, season = _weekday_and_season(rc_date)
    now = datetime.now().isoformat()

    cur.execute("""
        INSERT OR IGNORE INTO ingest_meta
        (race_id, rc_date, meet, rc_no, weekday, season, first_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (race_id, rc_date, meet, rc_no, weekday, season, now))


def _meta_update_expected_end(cur, race_id, hhmm):
    cur.execute("""
        UPDATE ingest_meta
        SET expected_end_hhmm = COALESCE(expected_end_hhmm, ?)
        WHERE race_id=?
    """, (hhmm, race_id))


def _meta_mark_confirmed(cur, race_id, confirmed_retry_count: int):
    now = datetime.now().isoformat()
    cur.execute("""
        UPDATE ingest_meta
        SET confirmed_at=?,
            confirmed_retry_count=?
        WHERE race_id=?
    """, (now, int(confirmed_retry_count), race_id))


def _current_retry_count_for(cur, rc_date, meet, rc_no) -> int:
    cur.execute("""
        SELECT retry_count
        FROM retry_queue
        WHERE rc_date=? AND meet=? AND rc_no=?
        LIMIT 1
    """, (rc_date, meet, rc_no))
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _to_int(v):
    try:
        return int(v)
    except Exception:
        return None
