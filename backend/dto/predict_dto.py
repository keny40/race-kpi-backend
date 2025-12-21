from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime, timezone


class DecisionDTO(BaseModel):
    label: str = Field(..., description="최종 예측 라벨 (예: P/B/PASS)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="0~1 신뢰도")


class ModelResultDTO(BaseModel):
    name: str = Field(..., description="모델 이름 (예: model_A)")
    label: str = Field(..., description="모델이 낸 라벨")
    score: float = Field(..., description="모델 원 점수/확률")
    weight: float = Field(1.0, description="모델 가중치")


class MetaDTO(BaseModel):
    timestamp: str = Field(..., description="UTC ISO-8601 문자열")
    version: str = Field("v1", description="응답 포맷 버전")


class PredictResponseDTO(BaseModel):
    request_id: str = Field(..., description="요청 식별자 (race_id 등)")
    status: Literal["OK"] = Field("OK", description="성공 상태 고정")
    decision: DecisionDTO
    models: List[ModelResultDTO]
    meta: MetaDTO


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_predict_response(
    request_id: str,
    decision_label: str,
    confidence: float,
    models: list[dict],
    version: str = "v1",
) -> PredictResponseDTO:
    return PredictResponseDTO(
        request_id=request_id,
        status="OK",
        decision=DecisionDTO(
            label=decision_label,
            confidence=confidence,
        ),
        models=[ModelResultDTO(**m) for m in models],
        meta=MetaDTO(timestamp=utc_iso(), version=version),
    )
