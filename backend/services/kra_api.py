import requests
import os

KRA_API_URL = "https://apis.data.go.kr/B551015/API299"
SERVICE_KEY = os.getenv("KRA_SERVICE_KEY")

def fetch_all_kra_results(rc_year=None, rc_month=None, rc_date=None, meet=None, rc_no=None):
    page_no = 1
    all_items = []

    while True:
        params = {
            "serviceKey": SERVICE_KEY,
            "pageNo": page_no,
            "numOfRows": 100,
            "_type": "json",
        }
        if rc_year: params["rc_year"] = rc_year
        if rc_month: params["rc_month"] = rc_month
        if rc_date: params["rc_date"] = rc_date
        if meet: params["meet"] = meet
        if rc_no: params["rc_no"] = rc_no

        res = requests.get(KRA_API_URL, params=params, timeout=10)
        res.raise_for_status()

        body = res.json().get("response", {}).get("body", {})
        items = body.get("items", {}).get("item", [])

        if not items:
            break

        if isinstance(items, dict):
            items = [items]

        all_items.extend(items)

        if len(items) < 100:
            break

        page_no += 1

    return all_items
