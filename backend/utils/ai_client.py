# backend/utils/ai_client.py

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
import math

# ---------------------------------------------------------------------
# Redis가 없어도 돌아가도록: 있으면 사용, 없으면 메모리 버전으로 대체
# ---------------------------------------------------------------------


class _InMemoryListStore:
    """Redis 리스트 기능만 아주 간단히 흉내 내는 인메모리 스토어"""

    def __init__(self) -> None:
        self.store: Dict[str, List[Any]] = {}

    def lpush(self, key: str, value: Any) -> None:
        self.store.setdefault(key, [])
        self.store[key].insert(0, value)

    def ltrim(self, key: str, start: int, end: int) -> None:
        arr = self.store.get(key, [])
        if not arr:
            return
        if end < 0:
            end = len(arr) - 1
        self.store[key] = arr[start : end + 1]

    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        arr = self.store.get(key, [])
        if not arr:
            return []
        if end < 0 or end >= len(arr):
            end = len(arr) - 1
        return arr[start : end + 1]

    def llen(self, key: str) -> int:
        return len(self.store.get(key, []))


try:
    import redis  # type: ignore

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )
except Exception:
    # redis 패키지가 없거나 사용 불가하면 메모리 스토어로 대체
    redis_client = _InMemoryListStore()  # type: ignore


# ---------------------------------------------------------------------
# 상수 설정
# ---------------------------------------------------------------------

WINDOW_SIZE = 50  # 최근 몇 경기 기준으로 볼지
BASE_WEIGHT = 1.0
MIN_WEIGHT = 0.60
MAX_WEIGHT = 1.40

TIMELINE_MAX = 500  # 타임라인 최대 저장 개수


# ---------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------


def _model_history_key(model_name: str) -> str:
    return f"model:{model_name}:history"


def _prediction_timeline_key() -> str:
    return "predictions:timeline"


# ---------------------------------------------------------------------
# 모델 호출 (현재는 데모용 스텁)
# ---------------------------------------------------------------------


def call_model_A(race_id: int, horses: List[int]) -> Dict[str, Any]:
    # TODO: 실제 모델 A 호출로 교체
    return {
        "label": "B",
        "confidence": 0.95,
    }


def call_model_B(race_id: int, horses: List[int]) -> Dict[str, Any]:
    # TODO: 실제 모델 B 호출로 교체
    return {
        "label": "B",
        "confidence": 0.85,
    }


def call_model_C(race_id: int, horses: List[int]) -> Dict[str, Any]:
    # TODO: 실제 모델 C 호출로 교체
    return {
        "label": "B",
        "confidence": 0.90,
    }


# ---------------------------------------------------------------------
# weight 자동 조정 로직
# ---------------------------------------------------------------------


def _get_model_hit_rate(model_name: str) -> Optional[float]:
    """
    model_A / model_B / model_C 각각에 대해
    저장된 [1,0,1,...] hit/miss 값으로 적중률 계산
    """
    key = _model_history_key(model_name)
    values = redis_client.lrange(key, 0, WINDOW_SIZE - 1)
    if not values:
        return None

    hits = 0
    total = 0
    for v in values:
        try:
            hits += int(v)
            total += 1
        except Exception:
            continue

    if total <= 0:
        return None

    return hits / total


def get_model_weight(model_name: str) -> float:
    """
    최근 적중률 기반 동적 weight 계산

    - 로그 없으면 1.0
    - 샘플 5개 미만이면 1.0
    - hit_rate 0%  → 0.60
      hit_rate 50% → 1.00
      hit_rate 100%→ 1.40
    """
    hit_rate = _get_model_hit_rate(model_name)
    if hit_rate is None:
        return BASE_WEIGHT

    key = _model_history_key(model_name)
    sample_count = redis_client.llen(key)
    if sample_count < 5:
        return BASE_WEIGHT

    offset = hit_rate - 0.5  # -0.5 ~ +0.5
    weight = BASE_WEIGHT + offset * 0.8  # 0.6 ~ 1.4

    if weight < MIN_WEIGHT:
        weight = MIN_WEIGHT
    if weight > MAX_WEIGHT:
        weight = MAX_WEIGHT

    return round(weight, 2)


def log_feedback(actual_label: str, models: List[Dict[str, Any]]) -> None:
    """
    /api/result/feedback 에서 호출

    models = [
      {"name": "model_A", "label": "B"},
      {"name": "model_B", "label": "P"},
      ...
    ]
    """
    for m in models:
        name = m.get("name")
        if not name:
            continue

        pred = m.get("label")
        if pred in ("P", "B") and actual_label in ("P", "B"):
            hit = 1 if pred == actual_label else 0
        else:
            hit = 0

        key = _model_history_key(name)
        redis_client.lpush(key, hit)
        redis_client.ltrim(key, 0, WINDOW_SIZE - 1)


# 기존 코드 호환용 별칭들
save_feedback = log_feedback
record_feedback = log_feedback


def feedback(actual_label: str, models: List[Dict[str, Any]]) -> None:
    """
    옛날 코드에서 import feedback 으로 부를 수 있게 하는 래퍼
    """
    return log_feedback(actual_label, models)


# ---------------------------------------------------------------------
# 예측 결과 표준화 + 온도 보정 + 앙상블
# ---------------------------------------------------------------------


def _normalize_model_output(name: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    label = raw.get("label") or raw.get("prediction") or "PASS"
    confidence = float(raw.get("confidence", raw.get("prob", 0.5)))
    weight = get_model_weight(name)

    return {
        "name": name,
        "label": label,
        "score": confidence,
        "weight": weight,
    }


def _apply_temperature(p: float, temperature: float = 0.85) -> float:
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0

    logit = math.log(p / (1 - p))
    scaled = logit / max(temperature, 1e-6)
    prob = 1 / (1 + math.exp(-scaled))
    return prob


def ensemble(models: List[Dict[str, Any]]) -> Tuple[str, float]:
    bucket: Dict[str, float] = defaultdict(float)
    total = 0.0

    for m in models:
        label = m.get("label", "PASS")
        score = float(m.get("score", 0.5))
        weight = float(m.get("weight", 1.0))

        if label == "PASS":
            score *= 0.5

        s = score * weight
        bucket[label] += s
        total += s

    if not bucket or total <= 0:
        return "PASS", 0.0

    final_label = max(bucket, key=bucket.get)
    confidence = bucket[final_label] / total
    confidence = _apply_temperature(confidence, temperature=0.85)

    return final_label, round(confidence, 3)


# ---------------------------------------------------------------------
# 예측 로그 / 통계용 함수들
# ---------------------------------------------------------------------


def _log_prediction(
    race_id: int,
    horses: List[int],
    decision: Dict[str, Any],
    models: List[Dict[str, Any]],
) -> None:
    key = _prediction_timeline_key()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "race_id": race_id,
        "horses": horses,
        "label": decision.get("label"),
        "confidence": decision.get("confidence"),
        "models": models,
    }
    redis_client.lpush(key, json.dumps(entry))
    redis_client.ltrim(key, 0, TIMELINE_MAX - 1)


def get_prediction_timeline(limit: int = 50) -> List[Dict[str, Any]]:
    key = _prediction_timeline_key()
    raw_list = redis_client.lrange(key, 0, limit - 1)

    result: List[Dict[str, Any]] = []
    for item in raw_list:
        try:
            obj = json.loads(item)
            result.append(obj)
        except Exception:
            continue

    return result


def get_confidence_buckets() -> List[Dict[str, Any]]:
    buckets = [
        {"range": "50-60", "count": 0, "ratio": 0},
        {"range": "60-70", "count": 0, "ratio": 0},
        {"range": "70-80", "count": 0, "ratio": 0},
        {"range": "80-90", "count": 0, "ratio": 0},
        {"range": "90-100", "count": 0, "ratio": 0},
    ]

    timeline = get_prediction_timeline(limit=TIMELINE_MAX)

    def _bucket_index(c: float) -> Optional[int]:
        p = c * 100.0
        if p < 50:
            return None
        if p < 60:
            return 0
        if p < 70:
            return 1
        if p < 80:
            return 2
        if p < 90:
            return 3
        return 4

    total = 0
    for item in timeline:
        label = item.get("label")
        if label == "PASS":
            continue
        conf = item.get("confidence")
        if conf is None:
            continue

        idx = _bucket_index(float(conf))
        if idx is None:
            continue

        buckets[idx]["count"] += 1
        total += 1

    for b in buckets:
        if total > 0:
            b["ratio"] = round(b["count"] / total, 3)
        else:
            b["ratio"] = 0

    return buckets


# ---------------------------------------------------------------------
# 외부에서 사용하는 메인 엔트리포인트
# ---------------------------------------------------------------------


def request_prediction(race_id: int, horses: List[int]) -> Dict[str, Any]:
    raw_A = call_model_A(race_id, horses)
    raw_B = call_model_B(race_id, horses)
    raw_C = call_model_C(race_id, horses)

    models = [
        _normalize_model_output("model_A", raw_A),
        _normalize_model_output("model_B", raw_B),
        _normalize_model_output("model_C", raw_C),
    ]

    final_label, final_confidence = ensemble(models)

    decision = {
        "label": final_label,
        "confidence": final_confidence,
    }

    _log_prediction(race_id, horses, decision, models)

    return {
        "decision": decision,
        "models": models,
        "meta": {
            "race_id": race_id,
            "horses": horses,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
