import threading
import time
from datetime import datetime
from typing import Optional

from backend.services.db import get_conn
from backend.services.pre_race_risk_guard import risk_level, should_auto_resume
from backend.services.pre_race_history_store import save_pre_race_history
# sfrom backend.services.notify import notify_slack  # 없으면 import 제거
# 실제 pre-race 예측 함수로 교체하세요
from backend.services.pre_race_predict import run_pre_race_predict  # ← 프로젝트 실제 함수명에 맞게


# =========================
# Scheduler State
# =========================
_state = {
    "running": False,
    "paused": False,
    "thread": None,
    "interval_sec": 60,   # 기본 60초
}


# =========================
# Settings Loader (핵심)
# =========================
def load_settings() -> dict:
    """
    실행 직전마다 호출
    재시작 없이 룰 즉시 반영
    """
    conn = get_conn()
    row = conn.execute(
        """
        SELECT confidence_threshold, auto_pause
        FROM pre_race_settings
        LIMIT 1
        """
    ).fetchone()

    # 안전 기본값
    return {
        "confidence_threshold": float(row["confidence_threshold"]) if row else 0.65,
        "auto_pause": int(row["auto_pause"]) if row else 1,
    }


# =========================
# Control
# =========================
def start(interval_sec: Optional[int] = None):
    if _state["running"]:
        return {"ok": True, "status": "already_running"}

    if interval_sec is not None:
        _state["interval_sec"] = int(interval_sec)

    _state["running"] = True
    _state["paused"] = False

    t = threading.Thread(target=_loop, daemon=True)
    _state["thread"] = t
    t.start()
    return {"ok": True, "status": "started"}


def stop():
    _state["running"] = False
    return {"ok": True, "status": "stopped"}


def pause(reason: str = ""):
    _state["paused"] = True
    if reason:
        try:
            notify_slack(f"[PRE-RACE PAUSE] {reason}")
        except Exception:
            pass


def resume(reason: str = ""):
    _state["paused"] = False
    if reason:
        try:
            notify_slack(f"[PRE-RACE RESUME] {reason}")
        except Exception:
            pass


# =========================
# Loop
# =========================
def _loop():
    while _state["running"]:
        try:
            _tick()
        except Exception as e:
            # 치명 에러 방지: 루프 유지
            try:
                notify_slack(f"[PRE-RACE ERROR] {e}")
            except Exception:
                pass
        time.sleep(_state["interval_sec"])


def _tick():
    # 1) 실행 직전 룰 즉시 로드
    settings = load_settings()
    threshold = settings["confidence_threshold"]
    auto_pause_on = bool(settings["auto_pause"])

    # 2) 위험 단계 판단 (WARN/PAUSE/NORMAL)
    level = risk_level()

    if auto_pause_on:
        if level == "PAUSE":
            pause("risk_level=PAUSE")
            return
        if _state["paused"] and should_auto_resume():
            resume("confidence recovered")

    if _state["paused"]:
        return

    # 3) pre-race 예측 실행 (프로젝트 실제 함수로 연결)
    result = run_pre_race_predict()
    # result 예시:
    # {
    #   "race_id": "RACE_20260106_01",
    #   "scores": [{"horse_no":3,"score":0.82}, ...],
    #   "confidence": 0.78,
    #   "summary": {...}
    # }

    race_id = result["race_id"]
    confidence = float(result["confidence"])
    summary = result.get("summary", {})

    # 4) decision은 서버 룰 기준으로 즉시 반영
    decision = "BET" if confidence >= threshold else "PASS"

    # 5) 히스토리 저장 (정석)
    save_pre_race_history(
        race_id=race_id,
        summary=summary,
        confidence=confidence,
        decision=decision,
    )


# =========================
# Admin Aliases (선택)
# =========================
def start_scheduler():
    return start()

def stop_scheduler():
    return stop()
