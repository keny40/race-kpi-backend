import requests
import xml.etree.ElementTree as ET

SERVICE_KEY = "여기에_발급받은_serviceKey_그대로_붙여넣기"

URL = "https://apis.data.go.kr/B551015/API299"

params = {
    "serviceKey": SERVICE_KEY,
    "pageNo": 1,
    "numOfRows": 100,
    "meet": 1,          # 1=서울
    "rc_year": 2023,
    "rc_month": 202306,
    "_type": "xml",
}

resp = requests.get(URL, params=params, timeout=10)
resp.raise_for_status()

root = ET.fromstring(resp.text)

items = root.findall(".//item")
print(f"수신 경주 수: {len(items)}")

for it in items[:3]:
    print({
        "rcDate": it.findtext("rcDate"),
        "rcNo": it.findtext("rcNo"),
        "hrName": it.findtext("hrName"),
        "ord": it.findtext("ord"),
        "winOdds": it.findtext("winOdds"),
    })
