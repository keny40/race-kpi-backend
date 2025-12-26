# backend/services/state_manager.py

def get_current_state() -> str:
    """
    실제로는 DB / KPI 기준으로 판단
    현재는 예시
    """
    return "RED"   # 테스트용 (실운영에서는 동적 계산)
