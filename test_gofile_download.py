import urllib.request
import json
import zipfile
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# 1. Create account to get token
req1 = urllib.request.Request('https://api.gofile.io/accounts', data=b'{}', headers={**headers, 'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req1) as r1:
    res1 = json.loads(r1.read().decode('utf-8'))
    token = res1['data']['token']
    print("[+] Account token:", token)

# 2. Download direct file link WITH accountToken cookie
direct_url = "https://store-na-phx-4.gofile.io/download/web/731c2822-ed2e-435b-9878-23ed268d23fe/ota-extract-20260813-155536.zip"
output_file = "downloaded_test.zip"

req2 = urllib.request.Request(
    direct_url,
    headers={
        **headers,
        'Cookie': f'accountToken={token}',
        'Referer': 'https://gofile.io/'
    }
)

print(f"[*] Downloading from {direct_url}...")
with urllib.request.urlopen(req2) as resp, open(output_file, 'wb') as f:
    f.write(resp.read())

size = os.path.getsize(output_file)
print(f"[+] Download complete! File size: {size} bytes ({size / 1024 / 1024:.2f} MB)")
print("Is zipfile?", zipfile.is_zipfile(output_file))
