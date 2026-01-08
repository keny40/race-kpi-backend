# backend/services/data_source.py

"""
입력 데이터 소스 관리 모듈

현재 단계에서는
- REAL 크롤링
- 실패 알림
- 운영 연동

을 모두 사용하지 않고,
predict API 및 스케줄러 최소 동작만 보장합니다
"""

from typing import Dict, Any


def get_input_payload(race_id: str) -> Dict[str, Any]:
    """
    예측 입력 payload 생성

    현재는 MOCK 기반 최소 입력만 반환
    (predict 파이프라인 정상 동작 목적)
    """

    return {
        "race_id": race_id,
        "horses": [],
        "meta": {
            "source": "mock",
        },
    }
