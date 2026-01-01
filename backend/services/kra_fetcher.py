import os
from backend.services.mock_race_data import get_mock_race
from backend.services.kra_html_fetcher import fetch_latest_race_from_html

DATA_SOURCE = os.getenv("DATA_SOURCE", "MOCK").upper()  # MOCK | REAL

def fetch_latest_race():
    """
    REAL(HTML) → 실패 시 MOCK 폴백
    """
    if DATA_SOURCE == "REAL":
        real = fetch_latest_race_from_html()
        if real:
            return real

    return get_mock_race()
