"""GoFile URL resolver for resolving direct download URLs from gofile.io links."""

import re
import json
import requests
from urllib.parse import urlparse
from typing import Optional
from .base import BaseResolver, ResolvedURL


class GoFileResolver(BaseResolver):
    """Resolver for gofile.io download links."""

    def can_handle(self, url: str) -> bool:
        return "gofile.io/d/" in url or "gofile.io/c/" in url

    def resolve(self, url: str) -> ResolvedURL:
        match = re.search(r'gofile\.io/[dc]/([a-zA-Z0-9_-]+)', url)
        if not match:
            raise ValueError(f"Could not extract GoFile content ID from URL: {url}")
        content_id = match.group(1)

        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Origin": "https://gofile.io",
            "Referer": "https://gofile.io/"
        }

        # Step 1: Create guest token
        token = None
        try:
            res_acc = session.post("https://api.gofile.io/accounts", json={}, headers=headers, timeout=10)
            if res_acc.status_code == 200:
                acc_data = res_acc.json()
                if acc_data.get("status") == "ok":
                    token = acc_data.get("data", {}).get("token")
        except Exception:
            pass

        # Step 2: Fetch folder contents
        req_headers = headers.copy()
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        content_url = f"https://api.gofile.io/contents/{content_id}"
        res_content = session.get(content_url, headers=req_headers, timeout=10)
        res_content.raise_for_status()
        data = res_content.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"GoFile API error for folder {content_id}: {data}")

        children = data.get("data", {}).get("children", {})
        if not children:
            raise RuntimeError(f"No files found in GoFile folder {content_id}")

        first_child = next(iter(children.values()))
        direct_url = first_child.get("link")
        if not direct_url:
            raise RuntimeError(f"No direct link found for file in GoFile folder {content_id}")

        filename = first_child.get("name") or f"gofile_{content_id}.zip"
        file_size = first_child.get("size")

        cookies = {}
        if token:
            cookies["accountToken"] = token

        return ResolvedURL(
            original_url=url,
            direct_url=direct_url,
            filename=filename,
            file_size=file_size,
            headers=headers,
            cookies=cookies,
            supports_ranges=True
        )
