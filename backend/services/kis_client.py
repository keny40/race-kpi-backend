# backend/services/kis_client.py
import os
import time
import json
import requests
from typing import Optional, Dict, Any

KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")

# 계좌
KIS_CANO = os.getenv("KIS_CANO", "")          # 8자리 계좌번호
KIS_ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD", "01")  # 보통 01

# TR ID (실전/모의는 계정/환경에 따라 다를 수 있어 env로 분리)
KIS_TR_ID_BUY = os.getenv("KIS_TR_ID_BUY", "TTTC0802U")   # 현금매수 예시
KIS_TR_ID_SELL = os.getenv("KIS_TR_ID_SELL", "TTTC0801U") # 현금매도 예시

# 간단 토큰 캐시
_token_cache = {"access_token": None, "exp": 0.0}


def _now() -> float:
    return time.time()


def get_access_token(force: bool = False) -> str:
    """
    /oauth2/tokenP 로 접근토큰 발급/캐시
    """
    if (not force) and _token_cache["access_token"] and _token_cache["exp"] > _now() + 30:
        return _token_cache["access_token"]

    if not KIS_APP_KEY or not KIS_APP_SECRET:
        raise RuntimeError("KIS_APP_KEY / KIS_APP_SECRET env missing")

    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()

    token = data.get("access_token")
    expires = int(data.get("expires_in", 0))
    if not token or not expires:
        raise RuntimeError(f"tokenP bad response: {data}")

    _token_cache["access_token"] = token
    _token_cache["exp"] = _now() + expires
    return token


def get_hashkey(body: Dict[str, Any]) -> Optional[str]:
    """
    /uapi/hashkey (선택) : POST 바디 무결성용
    """
    try:
        token = get_access_token()
        url = f"{KIS_BASE_URL}/uapi/hashkey"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        }
        r = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        r.raise_for_status()
        return r.json().get("HASH")
    except Exception:
        return None


def place_order_cash(
    side: str,  # "BUY" | "SELL"
    code: str,  # 종목코드 6자리
    qty: int,
    price: int,  # 지정가, 시장가면 별도 처리 필요
) -> Dict[str, Any]:
    """
    국내주식 주문(현금) /uapi/domestic-stock/v1/trading/order-cash
    """
    if not KIS_CANO:
        raise RuntimeError("KIS_CANO env missing")
    if not KIS_ACNT_PRDT_CD:
        raise RuntimeError("KIS_ACNT_PRDT_CD env missing")

    token = get_access_token()
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"

    tr_id = KIS_TR_ID_BUY if side.upper() == "BUY" else KIS_TR_ID_SELL

    body = {
        "CANO": KIS_CANO,
        "ACNT_PRDT_CD": KIS_ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "00",          # 00: 지정가(일반적으로)
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": str(int(price)),
    }

    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
    }

    hk = get_hashkey(body)
    if hk:
        headers["hashkey"] = hk

    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
    r.raise_for_status()
    return r.json()
