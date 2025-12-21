from datetime import datetime, timedelta
from .endtime_estimator import estimate_expected_end_hhmm

MIN_DELAY_MINUTES = 8

def is_after_expected_end(
    rc_date: str,
    meet: int,
    rc_no: int,
    exp_end_hhmm: str | None
) -> bool:
    """
    exp_end_hhmm이 없으면 meet+rc_no 평균 종료시각으로 추정
    """
    if not rc_date or not meet or not rc_no:
        return False

    hhmm = exp_end_hhmm if exp_end_hhmm else estimate_expected_end_hhmm(rc_date, meet, rc_no)
    end_dt = datetime.strptime(rc_date + hhmm, "%Y%m%d%H%M")
    return datetime.now() >= end_dt + timedelta(minutes=MIN_DELAY_MINUTES)
