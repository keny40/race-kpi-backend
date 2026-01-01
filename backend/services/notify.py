import os
import json
import requests
from typing import Any, Dict, Optional

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

def _top_contrib(contrib: Dict[str, Any], n: int = 2) -> str:
    items = []
    for k, v in (contrib or {}).items():
        try:
            items.append((k, float(v)))
        except Exception:
            continue
    items.sort(key=lambda x: x[1], reverse=True)
    return ", ".join([f"{k}={v:.3f}" for k, v in items[:n]]) if items else "n/a"

def send_slack(text: str, extra: Optional[Dict[str, Any]] = None) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": text}
    if extra:
        payload["attachments"] = [{"text": json.dumps(extra, ensure_ascii=False)[:1500]}]
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=6)
    except Exception:
        pass

def notify_auto_pause(race_id: str, risk: Dict[str, Any]) -> None:
    top = _top_contrib(risk.get("contrib") or {})
    score = float(risk.get("score") or 0.0)
    thr = float(risk.get("threshold") or 0.0)
    streak = int(risk.get("red_streak") or 0)
    reason = str(risk.get("reason") or "AUTO_PAUSE")
    send_slack(
        f"🟥 AUTO_PAUSE 발생: {reason}\nrace={race_id} score={score:.3f} thr={thr:.3f} streak={streak}\nTOP: {top}",
        extra={"risk": risk}
    )

def notify_resume(mode: str, note: str = "") -> None:
    send_slack(f"🟩 RESUME: {mode} {note}".strip())
