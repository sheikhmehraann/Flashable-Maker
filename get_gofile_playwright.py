import sys
import json
from playwright.sync_api import sync_playwright

def resolve_gofile_url(url):
    print(f"[*] Launching Playwright to capture network requests for: {url}", flush=True)
    captured_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        def handle_response(response):
            try:
                if "api.gofile.io/contents" in response.url:
                    print(f"[+] Intercepted API response from: {response.url}", flush=True)
                    data = response.json()
                    children = data.get("data", {}).get("children", {})
                    for child_id, child in children.items():
                        link = child.get("link")
                        name = child.get("name")
                        if link:
                            print(f"[FOUND DIRECT LINK] {name} -> {link}", flush=True)
                            captured_links.append((name, link))
            except Exception as e:
                pass

        page.on("response", handle_response)
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"[!] Navigation notice: {e}", flush=True)

        browser.close()
    return captured_links

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://gofile.io/d/VDm7s5bu"
    links = resolve_gofile_url(target_url)
    print("\nFINAL CAPTURED LINKS:", links, flush=True)
