import urllib.request
import re

req = urllib.request.Request('https://gofile.io/js/wt.obf.js', headers={'User-Agent': 'Mozilla/5.0'})
code = urllib.request.urlopen(req).read().decode('utf-8')

# Search for any hardcoded strings or key constants
matches = re.findall(r'["\']([a-zA-Z0-9_-]{10,60})["\']', code)
print("Unique string constants found:")
for m in sorted(set(matches))[:30]:
    print(" -", m)
