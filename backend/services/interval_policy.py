import sqlite3

DB_PATH = "races.db"

def compute_next_interval_minutes(default_minutes: int = 10) -> int:
    """
    retry_queue 상태로 다음 실행 간격을 자동 결정
    - 큐 많고 평균 retry 높으면 간격을 늘려 API/서버 부하 + 중복시도 감소
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*), AVG(retry_count) FROM retry_queue")
    total, avg_retry = cur.fetchone()
    con.close()

    avg_retry = avg_retry or 0

    # 보수적으로 운영
    if total >= 80 or avg_retry >= 3.0:
        return 30
    if total >= 30 or avg_retry >= 2.0:
        return 20
    if total >= 10 or avg_retry >= 1.0:
        return 15
    return default_minutes
