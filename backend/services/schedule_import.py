# backend/services/schedule_import.py
import csv
import io
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

# DB_PATH는 기존 프로젝트의 경로 규칙을 따르세요
# (대부분 backend/services/db.py에서 가져오지만, C 단계는 단독 투입 가능하게 최소 의존으로 작성)
DEFAULT_DB_PATH = "backend/races.db"


@dataclass
class RaceScheduleRow:
    race_date: str        # YYYYMMDD
    meet: int             # 1=서울 2=부경 3=제주(프로젝트 규칙에 맞게)
    race_no: int
    start_time: Optional[str] = None  # HH:MM
    pdf_url: Optional[str] = None
    note: Optional[str] = None


def _norm_date(s: str) -> str:
    s = s.strip()
    s = s.replace("-", "").replace(".", "").replace("/", "")
    if len(s) == 8 and s.isdigit():
        return s
    raise ValueError(f"invalid date: {s}")


def _norm_meet(s: str) -> int:
    s = s.strip()
    if s.isdigit():
        return int(s)
    s2 = s.lower()
    if "서울" in s or "seoul" in s2:
        return 1
    if "부산" in s or "부경" in s or "busan" in s2:
        return 2
    if "제주" in s or "jeju" in s2:
        return 3
    raise ValueError(f"invalid meet: {s}")


def _norm_race_no(s: str) -> int:
    s = s.strip()
    s = re.sub(r"[^\d]", "", s)
    if not s:
        raise ValueError("invalid race_no")
    return int(s)


def _norm_time(s: str) -> Optional[str]:
    s = (s or "").strip()
    if not s:
        return None
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})", s)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return f"{hh:02d}:{mm:02d}"
    return None


def make_race_id(race_date: str, meet: int, race_no: int) -> str:
    # 프로젝트의 race_id 규칙에 맞게 통일
    # 예: SEOUL_20260105_01 / BUSAN_... / JEJU_...
    meet_code = {1: "SEOUL", 2: "BUSAN", 3: "JEJU"}.get(meet, f"MEET{meet}")
    return f"{meet_code}_{race_date}_{race_no:02d}"


def ensure_tables(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_schedule (
        race_id TEXT PRIMARY KEY,
        race_date TEXT NOT NULL,
        meet INTEGER NOT NULL,
        race_no INTEGER NOT NULL,
        start_time TEXT,
        pdf_url TEXT,
        note TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 기존 프로젝트에서 races 테이블을 이미 쓰는 경우가 많아서,
    # 없으면 최소 컬럼으로 만들어둠(충돌 방지 위해 IF NOT EXISTS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS races (
        race_id TEXT PRIMARY KEY,
        race_date TEXT,
        meet INTEGER,
        race_no INTEGER,
        start_time TEXT,
        status TEXT DEFAULT 'SCHEDULED',
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def upsert_schedule(rows: List[RaceScheduleRow], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    ensure_tables(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now = datetime.utcnow().isoformat(timespec="seconds")

    upserted = 0
    for r in rows:
        race_id = make_race_id(r.race_date, r.meet, r.race_no)

        cur.execute("""
        INSERT INTO race_schedule (race_id, race_date, meet, race_no, start_time, pdf_url, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(race_id) DO UPDATE SET
            race_date=excluded.race_date,
            meet=excluded.meet,
            race_no=excluded.race_no,
            start_time=COALESCE(excluded.start_time, race_schedule.start_time),
            pdf_url=COALESCE(excluded.pdf_url, race_schedule.pdf_url),
            note=COALESCE(excluded.note, race_schedule.note)
        """, (race_id, r.race_date, r.meet, r.race_no, r.start_time, r.pdf_url, r.note, now))

        # races에도 반영(대시보드/스케줄러가 races를 보는 경우 대응)
        cur.execute("""
        INSERT INTO races (race_id, race_date, meet, race_no, start_time, status, updated_at)
        VALUES (?, ?, ?, ?, ?, 'SCHEDULED', ?)
        ON CONFLICT(race_id) DO UPDATE SET
            race_date=excluded.race_date,
            meet=excluded.meet,
            race_no=excluded.race_no,
            start_time=COALESCE(excluded.start_time, races.start_time),
            updated_at=excluded.updated_at
        """, (race_id, r.race_date, r.meet, r.race_no, r.start_time, now))

        upserted += 1

    conn.commit()
    conn.close()

    return {"ok": True, "upserted": upserted}


def parse_csv_text(csv_text: str) -> List[RaceScheduleRow]:
    """
    CSV 헤더 예시(권장):
      race_date, meet, race_no, start_time, pdf_url, note
    헤더가 없어도 대충 맞춰서 파싱 시도함
    """
    txt = (csv_text or "").strip()
    if not txt:
        return []

    f = io.StringIO(txt)
    sniff = csv.Sniffer()
    has_header = False
    try:
        has_header = sniff.has_header(txt[:2048])
    except Exception:
        has_header = False

    rows: List[RaceScheduleRow] = []

    if has_header:
        reader = csv.DictReader(f)
        for d in reader:
            rd = _norm_date(d.get("race_date", d.get("date", "")))
            meet = _norm_meet(d.get("meet", "1"))
            rn = _norm_race_no(d.get("race_no", d.get("race", "")))
            st = _norm_time(d.get("start_time", d.get("time", "")))
            pdf = (d.get("pdf_url") or d.get("pdf") or "").strip() or None
            note = (d.get("note") or "").strip() or None
            rows.append(RaceScheduleRow(rd, meet, rn, st, pdf, note))
        return rows

    # no header: date, meet, race_no, start_time, pdf_url
    reader2 = csv.reader(f)
    for cols in reader2:
        cols = [c.strip() for c in cols if c is not None]
        if not cols:
            continue
        if len(cols) < 3:
            continue
        rd = _norm_date(cols[0])
        meet = _norm_meet(cols[1])
        rn = _norm_race_no(cols[2])
        st = _norm_time(cols[3]) if len(cols) >= 4 else None
        pdf = cols[4].strip() if len(cols) >= 5 and cols[4].strip() else None
        rows.append(RaceScheduleRow(rd, meet, rn, st, pdf, None))

    return rows


def parse_paste_lines(paste_text: str, default_date: Optional[str] = None, default_meet: Optional[int] = None) -> List[RaceScheduleRow]:
    """
    메모장/복붙 11장(텍스트)에서 최소한 '경주번호'만 뽑아도 스케줄 테이블을 만들 수 있게 설계
    인식 패턴:
      - "1경주", "11경주"
      - "출발 12:35" / "12:35"
    """
    txt = (paste_text or "").strip()
    if not txt:
        return []

    if default_date:
        dd = _norm_date(default_date)
    else:
        # 텍스트에서 YYYYMMDD, YYYY-MM-DD, 2026.01.05 등 추출
        m = re.search(r"(20\d{2})[.\-/ ]?(0\d|1[0-2])[.\-/ ]?([0-2]\d|3[01])", txt)
        if m:
            dd = f"{m.group(1)}{m.group(2)}{m.group(3)}"
        else:
            raise ValueError("default_date가 필요합니다(텍스트에서 날짜를 못 찾음)")

    meet = default_meet if default_meet is not None else 1

    # 경주번호 후보들
    nums = set()
    for m in re.finditer(r"(\d{1,2})\s*경주", txt):
        nums.add(int(m.group(1)))

    # 시간 후보(경주번호별 매칭이 어려우면 대표 시간만 넣고 start_time은 비워도 됨)
    time_candidates = re.findall(r"(\d{1,2}\s*:\s*\d{2})", txt)
    time_candidates = [_norm_time(t) for t in time_candidates]
    time_candidates = [t for t in time_candidates if t]

    rows: List[RaceScheduleRow] = []
    for n in sorted(nums):
        st = None
        # 가장 앞의 시간 하나만 대표로 넣지 않고, 일단 비워둠(운영 안정화 우선)
        # 필요하면 UI/데이터 형식 맞추고 매칭 로직을 추가하면 됨
        rows.append(RaceScheduleRow(dd, meet, n, st, None, None))

    if not rows:
        raise ValueError("경주번호(1경주~)를 텍스트에서 찾지 못했습니다")

    return rows


def list_schedule_by_date(race_date: str, meet: Optional[int] = None, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    ensure_tables(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rd = _norm_date(race_date)
    if meet is None:
        rows = cur.execute("""
            SELECT race_id, race_date, meet, race_no, start_time, pdf_url, note
            FROM race_schedule
            WHERE race_date=?
            ORDER BY meet, race_no
        """, (rd,)).fetchall()
    else:
        rows = cur.execute("""
            SELECT race_id, race_date, meet, race_no, start_time, pdf_url, note
            FROM race_schedule
            WHERE race_date=? AND meet=?
            ORDER BY race_no
        """, (rd, int(meet))).fetchall()

    conn.close()
    return [dict(r) for r in rows]
