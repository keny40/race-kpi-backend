import requests

SERVICE_KEY = "실제_인증키"

url = "https://apis.data.go.kr/B551015/API299"
params = {
    "serviceKey": SERVICE_KEY,
    "rc_date": "20230604",
    "meet": 1,
    "_type": "xml"
}
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

r = requests.get(url, params=params, headers=headers, timeout=10)
print("STATUS:", r.status_code)
print(r.text[:1500])
