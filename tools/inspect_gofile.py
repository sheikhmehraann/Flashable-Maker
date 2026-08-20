import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Step 1: Create Account
req = urllib.request.Request(
    'https://api.gofile.io/accounts',
    data=b'{}',
    headers={**headers, 'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req) as resp:
        acc_data = json.loads(resp.read().decode('utf-8'))
        print("Account response:", acc_data)
        token = acc_data.get('data', {}).get('token')
        print("Token:", token)
except Exception as e:
    print("Account error:", e)
    token = None

# Step 2: Fetch wt token from wt.obf.js
req_wt = urllib.request.Request('https://gofile.io/js/wt.obf.js', headers=headers)
try:
    with urllib.request.urlopen(req_wt) as resp_wt:
        wt_code = resp_wt.read().decode('utf-8')
        print("wt.obf.js length:", len(wt_code))
        # Search for string literals or function names
        tokens = re.findall(r'"([a-zA-Z0-9]{15,40})"', wt_code)
        print("Found string tokens:", tokens[:10])
except Exception as e:
    print("wt.obf.js error:", e)

# Step 3: Query folder content with token header
req_folder = urllib.request.Request(
    'https://api.gofile.io/contents/VDm7s5bu?wt=4701870344',
    headers={**headers, 'Authorization': f'Bearer {token}'} if token else headers
)
try:
    with urllib.request.urlopen(req_folder) as resp_f:
        folder_data = json.loads(resp_f.read().decode('utf-8'))
        print("\nFolder Data:")
        print(json.dumps(folder_data, indent=2))
except Exception as e:
    print("\nFolder query error:", e)
