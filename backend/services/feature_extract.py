from __future__ import annotations

import re
from typing import Dict, Any


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def extract_features_from_html(html: str) -> Dict[str, Any]:
    # 1) text length
    text = _TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip()
    text_len = len(text)

    # 2) tables and rows (very rough but stable)
    table_count = len(re.findall(r"<table\b", html, flags=re.IGNORECASE))
    row_count = len(re.findall(r"<tr\b", html, flags=re.IGNORECASE))

    # 3) heuristics flags
    f_html_text_too_short = 1 if text_len < 3000 else 0
    f_table_count_low = 1 if table_count < 3 else 0
    f_row_count_low = 1 if row_count < 30 else 0

    return {
        "raw": {
            "text_len": text_len,
            "table_count": table_count,
            "row_count": row_count,
        },
        "flags": {
            "f_html_text_too_short": f_html_text_too_short,
            "f_table_count_low": f_table_count_low,
            "f_row_count_low": f_row_count_low,
        }
    }
