# backend/services/odds_provider.py
import os
import re
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any, List


@dataclass
class OddsResult:
    odds: Optional[float]
    confidence: float
    source: str
    reason: str


# ====== Config ======
DEFAULT_PDF_DIR = os.getenv("ODDS_PDF_DIR", "")  # 예: C:\Users\...\Horse Race\odds_pdfs
MAX_PDF_SCAN = int(os.getenv("ODDS_PDF_SCAN", "50"))  # 폴더에서 최신 N개만 스캔


# ====== Public API ======
def get_odds_for_race(race_id: str, horse_no: Any) -> OddsResult:
    """
    race_id 예: SEOUL_20260107_R05, TEST_RACE_001
    horse_no: decision(말 번호)
    """
    horse_no_int = _safe_int(horse_no)
    if horse_no_int is None:
        return OddsResult(None, 0.0, "none", "horse_no_invalid")

    # 1) TEST / 개발용 fallback
    if race_id.startswith("TEST_"):
        mock = {"TEST_RACE_001": {5: 2.0}}
        if race_id in mock and horse_no_int in mock[race_id]:
            return OddsResult(float(mock[race_id][horse_no_int]), 0.95, "mock", "mock_hit")
        return OddsResult(None, 0.0, "mock", "mock_miss")

    # 2) 실운영: PDF에서 odds 추출
    pdf_dir = DEFAULT_PDF_DIR
    if not pdf_dir or not os.path.isdir(pdf_dir):
        return OddsResult(None, 0.0, "none", "pdf_dir_missing")

    race_key = _parse_race_key(race_id)
    if race_key is None:
        return OddsResult(None, 0.0, "none", "race_id_unrecognized")

    track, yyyymmdd, race_no = race_key

    pdf_path = _find_best_pdf(pdf_dir, track, yyyymmdd, race_no)
    if not pdf_path:
        return OddsResult(None, 0.0, "none", "pdf_not_found")

    table = _parse_odds_from_pdf(pdf_path)

    # table key: (race_no, horse_no) or (None, horse_no) depending on pdf
    odds = None
    if (race_no, horse_no_int) in table:
        odds = table[(race_no, horse_no_int)]
        conf = 0.90
        reason = "exact_race_match"
    elif (None, horse_no_int) in table:
        odds = table[(None, horse_no_int)]
        conf = 0.65
        reason = "horse_only_match"
    else:
        return OddsResult(None, 0.40, os.path.basename(pdf_path), "odds_not_in_pdf")

    # 3) odds 신뢰도 체크(범위/이상치)
    verdict = validate_odds(odds, conf, source=os.path.basename(pdf_path), reason=reason)
    return verdict


def validate_odds(odds: Optional[float], confidence: float, source: str, reason: str) -> OddsResult:
    """
    운영 안전장치
    - odds는 1.0 이상이어야 의미 있음
    - 비정상적으로 큰 값(예: 999) 같은 파싱 오류 배제
    - confidence가 낮으면 None 처리(운영 판단에 섞지 않음)
    """
    if odds is None:
        return OddsResult(None, 0.0, source, "odds_none")

    try:
        o = float(odds)
    except Exception:
        return OddsResult(None, 0.0, source, "odds_not_float")

    if o < 1.0:
        return OddsResult(None, 0.0, source, "odds_too_small")

    if o > 200.0:
        return OddsResult(None, 0.0, source, "odds_too_large_parse_suspect")

    if confidence < 0.55:
        return OddsResult(None, confidence, source, "confidence_low_" + reason)

    return OddsResult(o, confidence, source, "ok_" + reason)


# ====== Helpers ======
def _safe_int(x: Any) -> Optional[int]:
    try:
        return int(str(x).strip())
    except Exception:
        return None


def _parse_race_key(race_id: str) -> Optional[Tuple[str, str, int]]:
    """
    기대 패턴: TRACK_YYYYMMDD_RNN
    예: SEOUL_20260107_R05
    """
    m = re.match(r"^([A-Z]+)_(\d{8})_R(\d{2})$", race_id.strip().upper())
    if not m:
        return None
    track = m.group(1)
    yyyymmdd = m.group(2)
    race_no = int(m.group(3))
    return track, yyyymmdd, race_no


def _find_best_pdf(pdf_dir: str, track: str, yyyymmdd: str, race_no: int) -> Optional[str]:
    """
    폴더에서 '가장 그럴듯한' PDF를 찾습니다
    - 파일명에 날짜/트랙/경주번호(R05 등)가 들어가면 우선
    - 없으면 최신 PDF 중에서 파싱 성공하는 걸 채택
    """
    files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not files:
        return None

    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    files = files[:MAX_PDF_SCAN]

    r_tag = f"R{race_no:02d}"
    track_u = track.upper()

    scored: List[Tuple[int, str]] = []
    for p in files:
        name = os.path.basename(p).upper()
        score = 0
        if yyyymmdd in name:
            score += 3
        if track_u in name:
            score += 2
        if r_tag in name:
            score += 3
        scored.append((score, p))

    scored.sort(key=lambda x: (x[0], os.path.getmtime(x[1])), reverse=True)
    best_score, best_path = scored[0]
    return best_path if best_score > 0 else scored[0][1]


def _parse_odds_from_pdf(pdf_path: str) -> Dict[Tuple[Optional[int], int], float]:
    """
    매우 보수적으로 파싱합니다
    - (race_no, horse_no) -> odds
    - race_no가 pdf에서 명확히 안 잡히면 (None, horse_no)로 저장
    """
    text = _extract_pdf_text(pdf_path)
    if not text:
        return {}

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    table: Dict[Tuple[Optional[int], int], float] = {}

    current_race_no: Optional[int] = None

    # race header 후보: "제5경주", "5경주", "R05" 등
    race_header_patterns = [
        re.compile(r"제?\s*(\d{1,2})\s*경주"),
        re.compile(r"\bR\s*0?(\d{1,2})\b", re.IGNORECASE),
    ]

    # odds row 후보: "5  3.1", "5번 3.1", "5  3.10" 등
    row_patterns = [
        re.compile(r"^\s*(\d{1,2})\s*(?:번)?\s+(\d+(?:\.\d+)?)\s*$"),
        re.compile(r"^\s*(\d{1,2})\s*-\s*(\d+(?:\.\d+)?)\s*$"),
    ]

    for ln in lines:
        # race header 갱신
        for pat in race_header_patterns:
            m = pat.search(ln)
            if m:
                try:
                    current_race_no = int(m.group(1))
                except Exception:
                    current_race_no = current_race_no
                break

        # odds row 매칭
        for rpat in row_patterns:
            m2 = rpat.match(ln)
            if not m2:
                continue

            horse_no = _safe_int(m2.group(1))
            if horse_no is None:
                continue

            try:
                odds = float(m2.group(2))
            except Exception:
                continue

            key = (current_race_no, horse_no) if current_race_no is not None else (None, horse_no)
            # 동일 키 중복이면 더 "그럴듯한" 값만 유지(극단치 제거)
            if key not in table:
                table[key] = odds
            else:
                prev = table[key]
                # 작은 값(보통 승식 배당)은 너무 크지 않음 → 평균에 가까운 쪽 선호
                if abs(odds - 3.0) < abs(prev - 3.0):
                    table[key] = odds

            break

    return table


def _extract_pdf_text(pdf_path: str) -> str:
    """
    pdfplumber 우선, 없으면 PyMuPDF(fitz) fallback
    """
    # 1) pdfplumber
    try:
        import pdfplumber  # type: ignore
        out = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t:
                    out.append(t)
        return "\n".join(out)
    except Exception:
        pass

    # 2) PyMuPDF
    try:
        import fitz  # type: ignore
        doc = fitz.open(pdf_path)
        out = []
        for i in range(len(doc)):
            out.append(doc[i].get_text("text"))
        return "\n".join(out)
    except Exception:
        return ""
