from datetime import datetime, timedelta

def create_fake_token(user_id: int) -> str:
    """간단한 데모용 토큰 (실서비스용 아님)"""
    expiry = (datetime.utcnow() + timedelta(hours=12)).isoformat()
    return f"fake-token-{user_id}-{expiry}"