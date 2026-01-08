# backend/services/horse_ai.py
import os
import re
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# =========================
# DB path helper
# =========================
def _default_db_path() -> str:
    """
    프로젝트에서 쓰는 races.db 위치를 최대한 자연스럽게 맞춤
    - 기본: backend/races.db
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
    return os.path.join(base_dir, "races.db")


# =========================
# Table init
# =========================
def init_horse_tables(db_path: Optional[str] = None) -> str:
    db_path = db_path or _default_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS horse_profile (
        horse_name TEXT PRIMARY KEY,
        rating1 REAL,
        rating2 REAL,
        rating3 REAL,
        rating4 REAL,
        age INTEGER,
        sex TEXT,
        origin TEXT,
        grade TEXT,
        stable_no INTEGER,
        starts INTEGER,
        wins INTEGER,
        seconds INTEGER,
        thirds INTEGER,
        total_prize_thousand INTEGER,
        last_race_date TEXT,  -- YYYY-MM-DD
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS horse_performance (
        horse_name TEXT PRIMARY KEY,
        period_from TEXT, -- YYYY-MM-DD
        period_to TEXT,   -- YYYY-MM-DD
        starts INTEGER,
        wins INTEGER,
        seconds INTEGER,
        thirds INTEGER,
        win_rate REAL,        -- 0~1
        quinella_rate REAL,   -- 0~1
        total_prize_won INTEGER,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS horse_scores (
        horse_name TEXT PRIMARY KEY,
        score REAL,
        r_norm REAL,
        win_rate REAL,
        quinella_rate REAL,
        eff_norm REAL,
        cond_penalty REAL,
        components_json TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()
    return db_path


# =========================
# Parsing helpers
# =========================
def _to_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, (int, float)) and not pd.isna(x):
        return int(x)
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    s = s.replace(",", "")
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else None


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)) and not pd.isna(x):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        m = re.search(r"-?\d+(\.\d+)?", s)
        return float(m.group(0)) if m else None


def _parse_last_race_date(cell: Any) -> Optional[str]:
    """
    예: '2025/12/28-11R' -> '2025-12-28'
    """
    if cell is None:
        return None
    s = str(cell).strip()
    if s == "" or s.lower() == "nan":
        return None
    m = re.search(r"(\d{4})/(\d{2})/(\d{2})", s)
    if not m:
        return None
    y, mo, d = m.group(1), m.group(2), m.group(3)
    return f"{y}-{mo}-{d}"


def _parse_record(cell: Any) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    '37(6/6/3)' -> starts=37, wins=6, seconds=6, thirds=3
    """
    if cell is None:
        return (None, None, None, None)
    s = str(cell).strip()
    if s == "" or s.lower() == "nan":
        return (None, None, None, None)

    m = re.match(r"(\d+)\s*\(\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*\)", s)
    if not m:
        # starts만이라도 있으면
        starts = _to_int(s)
        return (starts, None, None, None)
    starts = int(m.group(1))
    wins = int(m.group(2))
    seconds = int(m.group(3))
    thirds = int(m.group(4))
    return (starts, wins, seconds, thirds)


def _parse_period_from_to_from_header(df_raw: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    엑셀 상단에 '조회일자: 2025/01/01 ~ 2026/01/31' 같은 라인이 들어있는 경우가 있어
    판다스 기본 read_excel로는 보통 데이터만 나오지만,
    혹시라도 period가 컬럼으로 없을 때 대비용.
    여기서는 None 반환(현 파일은 period 정보가 표에는 없음).
    """
    return (None, None)


# =========================
# Loaders
# =========================
def load_horse_profile_xlsx(xlsx_path: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    HorseProfileList20260105.xlsx 로딩 (마명, 레이팅1~4, 성별/연령, 전적, 수득상금(천원), 최근출전일 등)
    """
    db_path = init_horse_tables(db_path)

    df = pd.read_excel(xlsx_path)

    required = ["마명", "레이팅1", "레이팅2", "레이팅3", "레이팅4", "성별", "연령", "산지", "등급", "조", "전적", "수득상금(천원)", "최근출전일"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[horse_profile] missing columns: {missing}")

    now = datetime.now().isoformat(timespec="seconds")

    rows = []
    for _, r in df.iterrows():
        horse_name = str(r["마명"]).strip()
        if not horse_name or horse_name.lower() == "nan":
            continue

        starts, wins, seconds, thirds = _parse_record(r.get("전적"))
        row = {
            "horse_name": horse_name,
            "rating1": _to_float(r.get("레이팅1")),
            "rating2": _to_float(r.get("레이팅2")),
            "rating3": _to_float(r.get("레이팅3")),
            "rating4": _to_float(r.get("레이팅4")),
            "age": _to_int(r.get("연령")),
            "sex": str(r.get("성별")).strip() if r.get("성별") is not None else None,
            "origin": str(r.get("산지")).strip() if r.get("산지") is not None else None,
            "grade": str(r.get("등급")).strip() if r.get("등급") is not None else None,
            "stable_no": _to_int(r.get("조")),
            "starts": starts,
            "wins": wins,
            "seconds": seconds,
            "thirds": thirds,
            "total_prize_thousand": _to_int(r.get("수득상금(천원)")),
            "last_race_date": _parse_last_race_date(r.get("최근출전일")),
            "updated_at": now,
        }
        rows.append(row)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany("""
    INSERT INTO horse_profile (
        horse_name, rating1, rating2, rating3, rating4,
        age, sex, origin, grade, stable_no,
        starts, wins, seconds, thirds,
        total_prize_thousand, last_race_date, updated_at
    ) VALUES (
        :horse_name, :rating1, :rating2, :rating3, :rating4,
        :age, :sex, :origin, :grade, :stable_no,
        :starts, :wins, :seconds, :thirds,
        :total_prize_thousand, :last_race_date, :updated_at
    )
    ON CONFLICT(horse_name) DO UPDATE SET
        rating1=excluded.rating1,
        rating2=excluded.rating2,
        rating3=excluded.rating3,
        rating4=excluded.rating4,
        age=excluded.age,
        sex=excluded.sex,
        origin=excluded.origin,
        grade=excluded.grade,
        stable_no=excluded.stable_no,
        starts=COALESCE(excluded.starts, horse_profile.starts),
        wins=COALESCE(excluded.wins, horse_profile.wins),
        seconds=COALESCE(excluded.seconds, horse_profile.seconds),
        thirds=COALESCE(excluded.thirds, horse_profile.thirds),
        total_prize_thousand=excluded.total_prize_thousand,
        last_race_date=excluded.last_race_date,
        updated_at=excluded.updated_at
    """, rows)

    conn.commit()
    conn.close()

    return {"ok": True, "db_path": db_path, "loaded": len(rows), "source": os.path.basename(xlsx_path)}


def load_horse_performance_xlsx(
    xlsx_path: str,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    scorePeriod50ObjectListExcelView.xlsx 로딩
    - 출전수, 1/2/3위, 승률/복승률, 수득상금(원) 기준
    """
    db_path = init_horse_tables(db_path)

    df = pd.read_excel(xlsx_path)

    required = ["마명", "출전수", "1위", "2위", "3위", "승률", "복승률", "수득상금"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[horse_performance] missing columns: {missing}")

    if not period_from or not period_to:
        pf, pt = _parse_period_from_to_from_header(df)
        period_from = period_from or pf
        period_to = period_to or pt

    now = datetime.now().isoformat(timespec="seconds")

    rows = []
    for _, r in df.iterrows():
        horse_name = str(r["마명"]).strip()
        if not horse_name or horse_name.lower() == "nan":
            continue

        starts = _to_int(r.get("출전수")) or 0
        wins = _to_int(r.get("1위")) or 0
        seconds = _to_int(r.get("2위")) or 0
        thirds = _to_int(r.get("3위")) or 0

        # 승률/복승률: 엑셀은 %값(예: 75.0) → 0~1로 변환
        win_rate = _to_float(r.get("승률"))
        quinella_rate = _to_float(r.get("복승률"))
        win_rate = (win_rate / 100.0) if win_rate is not None else None
        quinella_rate = (quinella_rate / 100.0) if quinella_rate is not None else None

        total_prize_won = _to_int(r.get("수득상금"))

        rows.append({
            "horse_name": horse_name,
            "period_from": period_from,
            "period_to": period_to,
            "starts": starts,
            "wins": wins,
            "seconds": seconds,
            "thirds": thirds,
            "win_rate": win_rate,
            "quinella_rate": quinella_rate,
            "total_prize_won": total_prize_won,
            "updated_at": now,
        })

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany("""
    INSERT INTO horse_performance (
        horse_name, period_from, period_to,
        starts, wins, seconds, thirds,
        win_rate, quinella_rate,
        total_prize_won, updated_at
    ) VALUES (
        :horse_name, :period_from, :period_to,
        :starts, :wins, :seconds, :thirds,
        :win_rate, :quinella_rate,
        :total_prize_won, :updated_at
    )
    ON CONFLICT(horse_name) DO UPDATE SET
        period_from=excluded.period_from,
        period_to=excluded.period_to,
        starts=excluded.starts,
        wins=excluded.wins,
        seconds=excluded.seconds,
        thirds=excluded.thirds,
        win_rate=excluded.win_rate,
        quinella_rate=excluded.quinella_rate,
        total_prize_won=excluded.total_prize_won,
        updated_at=excluded.updated_at
    """, rows)

    conn.commit()
    conn.close()

    return {"ok": True, "db_path": db_path, "loaded": len(rows), "source": os.path.basename(xlsx_path)}


# =========================
# Scoring
# =========================
def _minmax_norm(values: List[float]) -> Tuple[float, float]:
    if not values:
        return (0.0, 1.0)
    vmin = min(values)
    vmax = max(values)
    if abs(vmax - vmin) < 1e-9:
        return (vmin, vmax + 1.0)  # avoid zero division
    return (vmin, vmax)


def _clamp01(x: Optional[float]) -> float:
    if x is None:
        return 0.0
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return float(x)


def _days_since(yyyy_mm_dd: Optional[str]) -> Optional[int]:
    if not yyyy_mm_dd:
        return None
    try:
        d = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return None


def compute_and_store_horse_scores(
    db_path: Optional[str] = None,
    w_rating: float = 0.55,
    w_win: float = 0.25,
    w_quinella: float = 0.10,
    w_eff: float = 0.10,
    penalty_30: float = -0.05,
    penalty_60: float = -0.10
) -> Dict[str, Any]:
    """
    HorseScore =
      w_rating * R_norm
    + w_win * win_rate
    + w_quinella * quinella_rate
    + w_eff * eff_norm
    + cond_penalty
    """
    db_path = init_horse_tables(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # profile + performance left join
    rows = cur.execute("""
    SELECT
        p.horse_name,
        p.rating1, p.rating2, p.rating3, p.rating4,
        p.total_prize_thousand,
        p.last_race_date,
        pf.starts AS perf_starts,
        pf.win_rate,
        pf.quinella_rate,
        pf.total_prize_won
    FROM horse_profile p
    LEFT JOIN horse_performance pf
      ON p.horse_name = pf.horse_name
    """).fetchall()

    if not rows:
        conn.close()
        return {"ok": False, "reason": "no horse_profile rows", "db_path": db_path}

    # rating mean + eff 준비
    rating_means: List[float] = []
    eff_values: List[float] = []

    temp: List[Dict[str, Any]] = []
    for r in rows:
        r1, r2, r3, r4 = r["rating1"], r["rating2"], r["rating3"], r["rating4"]
        ratings = [x for x in [r1, r2, r3, r4] if x is not None]
        r_mean = float(sum(ratings) / len(ratings)) if ratings else 0.0

        # 효율: (프로필 상금 천원 → 원 환산) / (성과 출전수 or 전적 출전수)
        prize_won = None
        if r["total_prize_won"] is not None:
            prize_won = int(r["total_prize_won"])
        elif r["total_prize_thousand"] is not None:
            prize_won = int(r["total_prize_thousand"]) * 1000

        starts = r["perf_starts"] if r["perf_starts"] is not None else None
        if starts is None or starts <= 0:
            starts = None

        eff = None
        if prize_won is not None and starts:
            eff = prize_won / float(starts)

        rating_means.append(r_mean)
        if eff is not None:
            eff_values.append(float(eff))

        temp.append({
            "horse_name": r["horse_name"],
            "r_mean": r_mean,
            "win_rate": r["win_rate"],
            "quinella_rate": r["quinella_rate"],
            "eff": eff,
            "last_race_date": r["last_race_date"],
        })

    rmin, rmax = _minmax_norm(rating_means)
    emin, emax = _minmax_norm(eff_values) if eff_values else (0.0, 1.0)

    now = datetime.now().isoformat(timespec="seconds")

    out_rows = []
    for t in temp:
        r_norm = (t["r_mean"] - rmin) / (rmax - rmin) if (rmax - rmin) != 0 else 0.0
        r_norm = _clamp01(r_norm)

        win_rate = _clamp01(t["win_rate"])
        quinella_rate = _clamp01(t["quinella_rate"])

        eff_norm = 0.0
        if t["eff"] is not None and (emax - emin) != 0:
            eff_norm = (float(t["eff"]) - emin) / (emax - emin)
        eff_norm = _clamp01(eff_norm)

        # 컨디션 페널티
        cond_penalty = 0.0
        days = _days_since(t["last_race_date"])
        if days is not None:
            if days > 60:
                cond_penalty = penalty_60
            elif days > 30:
                cond_penalty = penalty_30

        score = (
            w_rating * r_norm
            + w_win * win_rate
            + w_quinella * quinella_rate
            + w_eff * eff_norm
            + cond_penalty
        )

        components = {
            "r_mean": t["r_mean"],
            "r_norm": r_norm,
            "win_rate": win_rate,
            "quinella_rate": quinella_rate,
            "eff_norm": eff_norm,
            "cond_penalty": cond_penalty,
            "weights": {"rating": w_rating, "win": w_win, "quinella": w_quinella, "eff": w_eff},
        }

        out_rows.append({
            "horse_name": t["horse_name"],
            "score": float(score),
            "r_norm": float(r_norm),
            "win_rate": float(win_rate),
            "quinella_rate": float(quinella_rate),
            "eff_norm": float(eff_norm),
            "cond_penalty": float(cond_penalty),
            "components_json": str(components),
            "updated_at": now,
        })

    cur.executemany("""
    INSERT INTO horse_scores (
        horse_name, score, r_norm, win_rate, quinella_rate, eff_norm, cond_penalty,
        components_json, updated_at
    ) VALUES (
        :horse_name, :score, :r_norm, :win_rate, :quinella_rate, :eff_norm, :cond_penalty,
        :components_json, :updated_at
    )
    ON CONFLICT(horse_name) DO UPDATE SET
        score=excluded.score,
        r_norm=excluded.r_norm,
        win_rate=excluded.win_rate,
        quinella_rate=excluded.quinella_rate,
        eff_norm=excluded.eff_norm,
        cond_penalty=excluded.cond_penalty,
        components_json=excluded.components_json,
        updated_at=excluded.updated_at
    """, out_rows)

    conn.commit()
    conn.close()

    return {"ok": True, "db_path": db_path, "scored": len(out_rows)}


def get_top_horse_scores(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    db_path = db_path or _default_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT horse_name, score, r_norm, win_rate, quinella_rate, eff_norm, cond_penalty, updated_at
    FROM horse_scores
    ORDER BY score DESC
    LIMIT ?
    """, (limit,)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_horse_score(horse_name: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db_path = db_path or _default_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    row = cur.execute("""
    SELECT *
    FROM horse_scores
    WHERE horse_name = ?
    """, (horse_name,)).fetchone()

    conn.close()
    return dict(row) if row else None
