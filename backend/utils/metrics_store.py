# backend/utils/metrics_store.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


LOG_PATH = Path("data") / "predictions_log.jsonl"


def _ensure_dir() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_prediction(rec: Dict) -> None:
    """
    예측 시점에 prediction 정보를 한 줄씩 저장 (JSONL)
    model_A / model_B / model_C 각각 한 줄씩 넣을 수 있습니다.
    """
    _ensure_dir()
    rec = dict(rec)
    rec.setdefault("timestamp_utc", datetime.now(timezone.utc).isoformat())

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _load_all() -> List[Dict]:
    if not LOG_PATH.exists():
        return []
    out: List[Dict] = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                # 깨진 라인은 무시
                continue
    return out


def upsert_feedback(prediction_id: str, feedback: str) -> None:
    """
    같은 prediction_id 를 가진 모든 레코드(model_A/B/C)에
    동일한 feedback(hit/miss/pass)을 반영합니다.
    """
    _ensure_dir()
    recs = _load_all()
    now = datetime.now(timezone.utc).isoformat()

    changed = False
    for r in recs:
        if r.get("prediction_id") == prediction_id:
            r["feedback"] = feedback
            r["feedback_timestamp_utc"] = now
            changed = True

    # 해당 prediction_id를 못 찾은 경우, 최소 1줄은 남겨둠
    if not changed:
        recs.append(
            {
                "prediction_id": prediction_id,
                "feedback": feedback,
                "timestamp_utc": now,
                "feedback_timestamp_utc": now,
                "is_primary": True,
            }
        )

    with LOG_PATH.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_recent(limit: int = 200) -> List[Dict]:
    """
    최근 기록 기준으로 최대 limit개만 반환 (신규 → 오래된 순)
    """
    recs = _load_all()
    recs.sort(key=lambda r: r.get("timestamp_utc") or "", reverse=True)
    return recs[:limit]
