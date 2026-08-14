import json
import cloudscraper

scraper = cloudscraper.create_scraper()

# 1. Create account
r1 = scraper.post("https://api.gofile.io/accounts", json={})
print("Account status:", r1.status_code)
token = r1.json().get("data", {}).get("token")
print("Token:", token)

# 2. Get folder contents
headers = {
    "Authorization": f"Bearer {token}",
    "Origin": "https://gofile.io",
    "Referer": "https://gofile.io/",
}

r2 = scraper.get("https://api.gofile.io/contents/VDm7s5bu", headers=headers)
print("Content status:", r2.status_code)
print(json.dumps(r2.json(), indent=2))
