import urllib.request
import json
import re
import sys

def resolve_gofile_link(url):
    m = re.search(r'gofile\.io/d/([a-zA-Z0-9]+)', url)
    if not m:
        return url
    content_id = m.group(1)
    print(f"[*] Resolving Gofile folder ID: {content_id}")
    try:
        req = urllib.request.Request(
            'https://api.gofile.io/accounts',
            data=b'{}',
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            token = data.get('data', {}).get('token')
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        req2 = urllib.request.Request(f'https://api.gofile.io/contents/{content_id}', headers=headers)
        with urllib.request.urlopen(req2) as resp2:
            data2 = json.loads(resp2.read().decode('utf-8'))
            children = data2.get('data', {}).get('children', {})
            for child_id, child in children.items():
                link = child.get('link')
                if link:
                    print(f"[+] Resolved direct download URL: {link}")
                    return link
    except Exception as e:
        print(f"[!] Gofile resolve error: {e}")
    return url

if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://gofile.io/d/VDm7s5bu"
    print("Resolved:", resolve_gofile_link(test_url))
