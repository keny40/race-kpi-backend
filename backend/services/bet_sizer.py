# backend/services/bet_sizer.py
import os
from typing import Dict, Any

# 전부 env로 안전하게 통제
BANKROLL = float(os.getenv("BANKROLL", "1000000"))              # 가상/실자본
MAX_PER_ORDER = float(os.getenv("MAX_PER_ORDER", "50000"))      # 1회 최대
MIN_PER_ORDER = float(os.getenv("MIN_PER_ORDER", "5000"))       # 1회 최소
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))      # 켈리 적용 비율(보수적)

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def size_from_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    입력 예시
    calibrated_confidence: 0~1
    roi: 기대 ROI(예: 0.08 => +8% 기대) 또는 없으면 0
    price: 단가(주식이면 주문가격)
    """
    p = float(signal.get("calibrated_confidence", signal.get("confidence", 0.0)) or 0.0)
    roi = float(signal.get("roi", 0.0) or 0.0)

    # 보수적으로 “엣지”를 낮게 잡음
    edge = max(0.0, (p - 0.5)) + max(0.0, roi) * 0.5

    # 켈리 느낌(완전 켈리 대신 매우 약하게)
    frac = clamp(edge * KELLY_FRACTION, 0.0, 0.2)

    budget = BANKROLL * frac
    budget = clamp(budget, MIN_PER_ORDER, MAX_PER_ORDER)

    # 주식 주문 수량 계산 (price 없으면 금액만 반환)
    price = signal.get("price")
    qty = None
    if price is not None:
        price = float(price)
        if price > 0:
            qty = int(budget // price)
            if qty <= 0:
                qty = 1

    return {
        "budget": float(budget),
        "qty": qty,
        "p": p,
        "roi": roi,
        "frac": frac,
    }
