# backend/services/kra_collector.py
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple

try:
    import requests
except Exception:
    requests = None

try:
    from bs4 import BeautifulSoup  # optional
except Exception:
    BeautifulSoup = None

KST = timezone(timedelta(hours=9))


def _now_kst() -> datetime:
    return datetime.now(tz=KST)


def _iso(dt: datetime) -> str:
    return dt.astimezone(KST).replace(microsecond=0).isoformat()


def _parse_start_time(s: str) -> Optional[str]:
    """
    다양한 포맷을 최대한 수용해서 ISO(KST)로 정규화
    기대 예시
    - 2026-01-05 14:30
    - 2026.01.05 14:30
    - 20260105 1430
    - 2026-01-05T14:30:00+09:00
    """
    if not s:
        return None

    s = s.strip()
    # ISO already
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return _iso(dt)
    except Exception:
        pass

    # 2026-01-05 14:30 / 2026.01.05 14:30
    m = re.search(r"(\d{4})[.\-\/](\d{2})[.\-\/](\d{2})\s+(\d{2}):(\d{2})", s)
    if m:
        y, mo, d, hh, mm = map(int, m.groups())
        dt = datetime(y, mo, d, hh, mm, tzinfo=KST)
        return _iso(dt)

    # 20260105 1430
    m = re.search(r"(\d{4})(\d{2})(\d{2})\s*(\d{2})(\d{2})", s)
    if m:
        y, mo, d, hh, mm = map(int, m.groups())
        dt = datetime(y, mo, d, hh, mm, tzinfo=KST)
        return _iso(dt)

    return None


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_races_table(db_path: str) -> None:
    """
    기존 races 테이블이 이미 있으면 건드리지 않고
    없으면 C 단계 최소 스키마로 생성
    """
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS races (
              race_id TEXT PRIMARY KEY,
              track TEXT,
              race_no INTEGER,
              start_time TEXT,
              title TEXT,
              raw_source TEXT,
              updated_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_races_start_time ON races(start_time)")
        conn.commit()
    finally:
        conn.close()


def upsert_races(db_path: str, races: List[Dict[str, Any]]) -> Dict[str, Any]:
    ensure_races_table(db_path)
    conn = _connect(db_path)
    inserted = 0
    updated = 0
    now = _iso(_now_kst())
    try:
        for r in races:
            race_id = str(r.get("race_id") or "").strip()
            if not race_id:
                continue

            track = (r.get("track") or "").strip() or None
            race_no = r.get("race_no")
            try:
                race_no = int(race_no) if race_no is not None else None
            except Exception:
                race_no = None

            start_time = _parse_start_time(str(r.get("start_time") or ""))  # ISO normalize
            title = (r.get("title") or "").strip() or None
            raw_source = (r.get("raw_source") or "").strip() or None

            # SQLite UPSERT
            row = conn.execute("SELECT 1 FROM races WHERE race_id=?", (race_id,)).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO races(race_id, track, race_no, start_time, title, raw_source, updated_at)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (race_id, track, race_no, start_time, title, raw_source, now),
                )
                inserted += 1
            else:
                conn.execute(
                    """
                    UPDATE races
                       SET track=?,
                           race_no=?,
                           start_time=?,
                           title=?,
                           raw_source=?,
                           updated_at=?
                     WHERE race_id=?
                    """,
                    (track, race_no, start_time, title, raw_source, now, race_id),
                )
                updated += 1

        conn.commit()
        return {"ok": True, "inserted": inserted, "updated": updated, "total": inserted + updated}
    finally:
        conn.close()


@dataclass
class KRACollectConfig:
    enabled: bool = True
    timeout_sec: int = 20
    user_agent: str = "Mozilla/5.0"
    races_url: str = ""  # e.g. https://... (운영에서 값 지정)
    mode: str = "REAL"   # REAL | MOCK


def _http_get(url: str, timeout_sec: int, user_agent: str) -> str:
    if requests is None:
        raise RuntimeError("requests_not_installed")
    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout_sec)
    resp.raise_for_status()
    return resp.text


def _parse_races_from_html(html: str) -> List[Dict[str, Any]]:
    """
    HTML 구조는 환경마다 다르므로,
    1) bs4 있으면 table/row 기반으로 최대 파싱 시도
    2) 없으면 정규식 기반 최소 파싱(레이스ID/시간)
    반환 형식: {race_id, start_time, track, race_no, title, raw_source}
    """
    races: List[Dict[str, Any]] = []

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")

        # 1) 테이블 기반 파싱 시도
        tables = soup.find_all("table")
        for tb in tables:
            rows = tb.find_all("tr")
            for tr in rows:
                tds = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
                if len(tds) < 3:
                    continue

                # 일반적으로 [장소/경주번호/출발시간/...] 패턴이 많음 → heuristics
                joined = " | ".join(tds)

                # race_id 후보: 영숫자/언더스코어/대시 길이 6+
                rid = None
                m = re.search(r"([A-Za-z0-9_\-]{6,})", joined)
                if m:
                    rid = m.group(1)

                # 시간 후보: yyyy-mm-dd hh:mm 혹은 hh:mm 단독
                start_time = None
                m = re.search(r"(\d{4}[.\-\/]\d{2}[.\-\/]\d{2}\s+\d{2}:\d{2})", joined)
                if m:
                    start_time = m.group(1)
                else:
                    # hh:mm 만 있으면 오늘 날짜 붙여서 저장(운영에서 URL이 당일 페이지면 유효)
                    m = re.search(r"(\d{2}:\d{2})", joined)
                    if m:
                        hhmm = m.group(1)
                        today = _now_kst().strftime("%Y-%m-%d")
                        start_time = f"{today} {hhmm}"

                # 트랙 후보
                track = None
                for cand in tds[:3]:
                    if any(k in cand for k in ["서울", "부산", "제주", "Seoul", "Busan", "Jeju"]):
                        track = cand
                        break

                # 경주번호 후보
                race_no = None
                for cand in tds:
                    m2 = re.search(r"(\d+)\s*R", cand, re.IGNORECASE)
                    if m2:
                        race_no = int(m2.group(1))
                        break

                # rid가 너무 약하면 스킵
                if not rid or not start_time:
                    continue

                races.append(
                    {
                        "race_id": rid,
                        "start_time": start_time,
                        "track": track,
                        "race_no": race_no,
                        "title": None,
                        "raw_source": "KRA_HTML",
                    }
                )

        if races:
            return races

    # 2) regex 최소 파싱 (fallback)
    # race_id 비슷한 토큰 + 시간 토큰을 근접 매칭하는 방식
    rid_candidates = re.findall(r"\b([A-Za-z0-9_\-]{8,})\b", html)
    time_candidates = re.findall(r"(\d{2}:\d{2})", html)

    if rid_candidates and time_candidates:
        today = _now_kst().strftime("%Y-%m-%d")
        # 1:1로 억지 매칭 (최소 동작용)
        n = min(len(rid_candidates), len(time_candidates), 20)
        for i in range(n):
            races.append(
                {
                    "race_id": rid_candidates[i],
                    "start_time": f"{today} {time_candidates[i]}",
                    "track": None,
                    "race_no": None,
                    "title": None,
                    "raw_source": "KRA_HTML_FALLBACK",
                }
            )
    return races


def collect_once(db_path: str, cfg: KRACollectConfig) -> Dict[str, Any]:
    """
    운영에서 반드시 env로 KRA_RACES_URL을 지정하세요
    (마사회 페이지는 지역/일자/세션에 따라 URL이 다릅니다)
    """
    if not cfg.enabled:
        return {"ok": True, "skipped": True, "reason": "disabled"}

    if cfg.mode.upper() == "MOCK":
        # MOCK은 즉시 end-to-end 확인용
        now = _now_kst()
        mock = [
            {"race_id": "MOCK_SEOUL_01", "start_time": _iso(now + timedelta(minutes=30)), "track": "서울", "race_no": 1, "title": "MOCK", "raw_source": "MOCK"},
            {"race_id": "MOCK_SEOUL_02", "start_time": _iso(now + timedelta(minutes=60)), "track": "서울", "race_no": 2, "title": "MOCK", "raw_source": "MOCK"},
        ]
        return {"ok": True, "mode": "MOCK", **upsert_races(db_path, mock)}

    if not cfg.races_url:
        return {"ok": False, "error": "KRA_RACES_URL_empty"}

    t0 = time.time()
    try:
        html = _http_get(cfg.races_url, cfg.timeout_sec, cfg.user_agent)
        parsed = _parse_races_from_html(html)
        if not parsed:
            return {"ok": False, "error": "parse_empty", "took_ms": int((time.time() - t0) * 1000)}
        res = upsert_races(db_path, parsed)
        res.update({"mode": "REAL", "took_ms": int((time.time() - t0) * 1000), "parsed": len(parsed)})
        return res
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{str(e)[:200]}", "took_ms": int((time.time() - t0) * 1000)}


def get_config_from_env() -> KRACollectConfig:
    return KRACollectConfig(
        enabled=(os.getenv("KRA_COLLECT_ENABLED", "1") == "1"),
        timeout_sec=int(os.getenv("KRA_COLLECT_TIMEOUT_SEC", "20")),
        user_agent=os.getenv("KRA_COLLECT_UA", "Mozilla/5.0"),
        races_url=os.getenv("KRA_RACES_URL", "").strip(),
        mode=os.getenv("KRA_COLLECT_MODE", "REAL").strip(),
    )
