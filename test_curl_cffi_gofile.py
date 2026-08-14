import json
from curl_cffi import requests

s = requests.Session(impersonate="chrome120")

# 1. Create account
r1 = s.post("https://api.gofile.io/accounts", json={})
print("Account status:", r1.status_code)
print(r1.text)

token = r1.json().get("data", {}).get("token")
print("Token:", token)

# 2. Get content
headers = {
    "Authorization": f"Bearer {token}",
    "Origin": "https://gofile.io",
    "Referer": "https://gofile.io/",
}

r2 = s.get("https://api.gofile.io/contents/VDm7s5bu", headers=headers)
print("Content status:", r2.status_code)
print(json.dumps(r2.json(), indent=2))
