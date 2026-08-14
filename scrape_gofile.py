import urllib.request
import re

url = "https://gofile.io/d/VDm7s5bu"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode('utf-8')

print("Page HTML snippet:")
print(html[:1500])

scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
print("\nFound scripts:", scripts)

for script in scripts:
    if not script.startswith('http'):
        script = 'https://gofile.io' + (script if script.startswith('/') else '/' + script)
    try:
        s_req = urllib.request.Request(script, headers={"User-Agent": "Mozilla/5.0"})
        s_text = urllib.request.urlopen(s_req).read().decode('utf-8')
        print(f"\n--- Checking {script} (Length: {len(s_text)}) ---")
        matches = re.findall(r'wt[":=]+([a-zA-Z0-9]+)', s_text)
        if matches:
            print("Matches:", matches)
        matches2 = re.findall(r'https://api\.gofile\.io[^\s"\']*', s_text)
        if matches2:
            print("API matches:", matches2[:5])
    except Exception as e:
        print(f"Error reading {script}: {e}")
