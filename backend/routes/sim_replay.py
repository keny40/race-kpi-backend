from fastapi import APIRouter, Query
from datetime import datetime
import time

from backend.services.mock_race_data import get_mock_race
from backend.services.simple_predictor import calculate_confidence
from backend.services.strategy_state import get_run_mode_status, set_run_mode_paused

router = APIRouter(prefix="/api/sim", tags=["sim"])


@router.post("/replay")
def replay(
    times: int = Query(50, ge=1, le=5000),
    sleep_ms: int = Query(0, ge=0, le=5000),
    red_threshold: float = Query(0.6, ge=0.0, le=1.0),
    auto_pause_after_reds: int = Query(10, ge=1, le=5000),
):
    """
    서버 내부에서 '가짜 과거경주'를 연속 재생하며 운영가드/RED 누적을 검증하는 엔드포인트
    - times 만큼 예측 반복
    - RED가 auto_pause_after_reds 이상 누적되면 자동 PAUSED 전환
    """
    st = get_run_mode_status()
    if st["paused"]:
        return {
            "status": "blocked",
            "detail": "PAUSED: sim blocked",
            "run_mode": st["run_mode"],
            "paused": st["paused"],
            "force_pass": st["force_pass"],
        }

    reds = 0
    blues = 0
    passes = 0
    events = []

    for i in range(times):
        st = get_run_mode_status()
        if st["paused"]:
            break

        race = get_mock_race()
        conf = calculate_confidence(race)

        if st["force_pass"]:
            decision = "PASS"
            passes += 1
        else:
            decision = "RED" if conf >= red_threshold else "BLUE"
            if decision == "RED":
                reds += 1
            else:
                blues += 1

        events.append({
            "i": i + 1,
            "race_id": race.get("race_id"),
            "decision": decision,
            "confidence": conf,
            "ts": datetime.utcnow().isoformat()
        })

        # AUTO PAUSE (운영 검증용)
        if reds >= auto_pause_after_reds:
            set_run_mode_paused()
            break

        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)

    st2 = get_run_mode_status()
    return {
        "status": "ok",
        "summary": {
            "times": times,
            "reds": reds,
            "blues": blues,
            "passes": passes,
            "auto_pause_after_reds": auto_pause_after_reds,
            "red_threshold": red_threshold,
            "sleep_ms": sleep_ms,
        },
        "run_mode": st2["run_mode"],
        "paused": st2["paused"],
        "force_pass": st2["force_pass"],
        "events_tail": events[-10:],  # 마지막 10개만 반환(브라우저 보기 좋게)
    }
