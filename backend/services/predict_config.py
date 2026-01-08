# backend/services/predict_config.py
PREDICT_CONFIG = {
    "enable_prestart_repredict": False,  # 기본 OFF
    "minutes_before_start": 10,          # n분 전
    "confidence_threshold": 0.60,        # PASS 기준선
}
