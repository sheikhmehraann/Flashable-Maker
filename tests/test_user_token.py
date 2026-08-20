import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import urllib.request
import json

token = "P3zpTTBczAE6qJrJ0JiaQyf8xEVtJRH4"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Authorization': f'Bearer {token}',
}

print("[*] Querying account details...")
req_acc = urllib.request.Request("https://api.gofile.io/accounts/me", headers=headers)
try:
    with urllib.request.urlopen(req_acc) as r:
        print("Account Me Info:", json.dumps(json.loads(r.read().decode('utf-8')), indent=2))
except Exception as e:
    print("Account Me error:", e)

print("\n[*] Querying folder VDm7s5bu contents...")
req_content = urllib.request.Request("https://api.gofile.io/contents/VDm7s5bu", headers=headers)
try:
    with urllib.request.urlopen(req_content) as r:
        content_data = json.loads(r.read().decode('utf-8'))
        print("Folder VDm7s5bu contents:")
        print(json.dumps(content_data, indent=2))
except Exception as e:
    print("Folder VDm7s5bu query error:", e)
