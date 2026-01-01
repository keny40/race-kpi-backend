# backend/services/real_crawler.py
import os
import re
import requests
from datetime import datetime
from typing import Dict, Any, Tuple

DEFAULT_TIMEOUT = 15


def _inject_date(url: str, date_str: str) -> str:
    # REAL_CRAWL_URL 에 {date}가 있으면 주입
    if "{date}" in url:
        return url.replace("{date}", date_str)
    return url


def fetch_html(date_str: str | None = None) -> Tuple[str, Dict[str, Any]]:
    """
    REAL_CRAWL_URL 환경변수 기준으로 HTML을 가져옵니다
    - REAL_CRAWL_URL 예: https://example.com/page?date={date}
    - date_str 없으면 오늘(YYYY-MM-DD) 사용
    """
    base_url = os.getenv("REAL_CRAWL_URL", "").strip()
    if not base_url:
        raise RuntimeError("REAL_CRAWL_URL is not set")

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    url = _inject_date(base_url, date_str)

    headers = {
        "User-Agent": os.getenv("CRAWL_UA", "Mozilla/5.0 (compatible; HorseRaceBot/1.0)"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    r = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()

    meta = {
        "url": url,
        "status_code": r.status_code,
        "bytes": len(r.content or b""),
    }
    return r.text, meta


def extract_features_from_html(html: str) -> Dict[str, Any]:
    """
    외부 feature_extract.py에 의존하지 않는 최소 feature 추출기
    UI/가드에서 쓰는 키를 고정합니다

    반환:
      - raw_features: {text_len, table_count, row_count}
      - flags: {f_html_text_too_short, f_table_count_low, f_row_count_low}
      - reason_codes: [HTML_TEXT_TOO_SHORT, TABLE_COUNT_LOW, ROW_COUNT_LOW]
    """
    # text_len: 태그 제거 후 길이
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text_len = len(text)

    # table_count: <table> 갯수
    table_count = len(re.findall(r"<table\b", html, flags=re.I))

    # row_count: <tr> 갯수
    row_count = len(re.findall(r"<tr\b", html, flags=re.I))

    # 기준값(필요하면 env로 조절)
    min_text = int(os.getenv("MIN_TEXT_LEN", "200"))
    min_table = int(os.getenv("MIN_TABLE_COUNT", "1"))
    min_row = int(os.getenv("MIN_ROW_COUNT", "5"))

    f_html_text_too_short = 1 if text_len < min_text else 0
    f_table_count_low = 1 if table_count < min_table else 0
    f_row_count_low = 1 if row_count < min_row else 0

    reason_codes = []
    if f_html_text_too_short:
        reason_codes.append("HTML_TEXT_TOO_SHORT")
    if f_table_count_low:
        reason_codes.append("TABLE_COUNT_LOW")
    if f_row_count_low:
        reason_codes.append("ROW_COUNT_LOW")

    return {
        "raw_features": {
            "text_len": text_len,
            "table_count": table_count,
            "row_count": row_count,
        },
        "flags": {
            "f_html_text_too_short": f_html_text_too_short,
            "f_table_count_low": f_table_count_low,
            "f_row_count_low": f_row_count_low,
        },
        "reason_codes": reason_codes,
    }
