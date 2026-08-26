#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ tools/resolve_gofile.py - GoFile Link Resolution & Diagnostic Tool ⚡
Usage:
    python tools/resolve_gofile.py https://gofile.io/d/J4nM4YE3
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gofile_transfer.resolvers.gofile import GoFileResolver
from gofile_transfer.token_generator import token_generator


def main():
    parser = argparse.ArgumentParser(description="GoFile Link Resolver & Diagnostic CLI")
    parser.add_argument("url", nargs="?", default="https://gofile.io/d/J4nM4YE3", help="GoFile link or folder ID")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    resolver = GoFileResolver()
    try:
        content_id = resolver.extract_content_id(args.url)
        token = resolver._get_account_token()
        wt = token_generator.generate_wt(token)

        resolved = resolver.resolve(args.url)

        if args.json:
            result = {
                "status": "success",
                "content_id": content_id,
                "token": token,
                "website_token": wt,
                "direct_url": resolved.direct_url,
                "filename": resolved.filename,
                "file_size": resolved.file_size,
                "headers": resolved.headers,
                "cookies": resolved.cookies
            }
            print(json.dumps(result, indent=2))
        else:
            print("═" * 65)
            print("         ⚡ GOFILE LINK RESOLUTION DIAGNOSTIC ⚡")
            print("═" * 65)
            print(f"[*] Input URL       : {args.url}")
            print(f"[+] Content ID      : {content_id}")
            print(f"[+] Account Token   : {token[:12]}...{token[-6:] if len(token) > 18 else ''}")
            print(f"[+] Website Token   : {wt}")
            print(f"[+] Filename        : {resolved.filename}")
            print(f"[+] Payload Size    : {f'{resolved.file_size / (1024*1024):.2f} MB' if resolved.file_size else 'Unknown'}")
            print(f"[+] Direct URL      : {resolved.direct_url}")
            print("═" * 65)

    except Exception as e:
        print(f"[!] Error resolving GoFile link '{args.url}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
