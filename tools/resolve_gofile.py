import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import urllib.request
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://gofile.io',
    'Referer': 'https://gofile.io/',
}

# 1. Account creation
req1 = urllib.request.Request(
    'https://api.gofile.io/accounts',
    data=b'{}',
    headers={**headers, 'Content-Type': 'application/json'},
    method='POST'
)

with urllib.request.urlopen(req1) as r1:
    res1 = json.loads(r1.read().decode('utf-8'))
    token = res1['data']['token']
    print("[+] Account token:", token)

# 2. Get folder contents using token query parameter AND wt param
url_contents = f'https://api.gofile.io/contents/VDm7s5bu?token={token}&wt=4701870344'
req2 = urllib.request.Request(url_contents, headers=headers)

with urllib.request.urlopen(req2) as r2:
    res2 = json.loads(r2.read().decode('utf-8'))
    print("[+] Gofile API Response:")
    print(json.dumps(res2, indent=2))
