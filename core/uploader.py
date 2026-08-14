#!/usr/bin/env python3
"""
Flashable-Engine: Cloud Uploader Module
Uploads generated flashable packages to Gofile.io, Transfer.sh, or other file hosts.
"""

import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
except ImportError:
    requests = None


class CloudUploader:
    """Handles automatic upload to high-speed hosting providers."""

    @staticmethod
    def upload_gofile(file_path: Path) -> Optional[str]:
        """Uploads file to Gofile.io and returns the public download link."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            print(f"[GOFILE] Error: File {file_path} does not exist.")
            return None

        print(f"\n[GOFILE] Uploading {file_path.name} ({file_path.stat().st_size / (1024*1024):.2f} MB) to Gofile.io...")

        # 1. Get Best Server
        server = "store1"
        try:
            req = urllib.request.Request("https://api.gofile.io/servers", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok" and data.get("data", {}).get("servers"):
                    server = data["data"]["servers"][0]["name"]
        except Exception as e:
            print(f"[GOFILE] Warning: Could not fetch server list ({e}), using default '{server}'")

        upload_url = f"https://{server}.gofile.io/contents/uploadfile"
        print(f"[GOFILE] Target Server: {server} ({upload_url})")

        # 2. Upload with requests (if available) or curl
        if requests:
            try:
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.name, f)}
                    response = requests.post(upload_url, files=files, timeout=600)
                    res_json = response.json()
                    if res_json.get("status") == "ok":
                        link = res_json["data"]["downloadPage"]
                        print(f"[GOFILE] ✅ Upload Successful! Download Page: {link}")
                        return link
                    else:
                        print(f"[GOFILE] API Error: {res_json}")
            except Exception as e:
                print(f"[GOFILE] Upload error via requests: {e}")

        # Fallback to curl
        import shutil
        import subprocess
        if shutil.which("curl"):
            try:
                cmd = ["curl", "-s", "-F", f"file=@{file_path}", upload_url]
                out = subprocess.check_output(cmd, timeout=600).decode("utf-8", errors="ignore")
                res_json = json.loads(out)
                if res_json.get("status") == "ok":
                    link = res_json["data"]["downloadPage"]
                    print(f"[GOFILE] ✅ Upload Successful! Download Page: {link}")
                    return link
            except Exception as e:
                print(f"[GOFILE] Fallback curl upload error: {e}")

        return None

    @staticmethod
    def upload_transfersh(file_path: Path) -> Optional[str]:
        """Uploads file to Transfer.sh."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            return None

        print(f"\n[TRANSFER.SH] Uploading {file_path.name}...")
        import shutil
        import subprocess
        if shutil.which("curl"):
            try:
                cmd = ["curl", "-s", "--upload-file", str(file_path), f"https://transfer.sh/{file_path.name}"]
                link = subprocess.check_output(cmd, timeout=300).decode("utf-8").strip()
                print(f"[TRANSFER.SH] ✅ Upload Successful! Download Link: {link}")
                return link
            except Exception as e:
                print(f"[TRANSFER.SH] Upload error: {e}")
        return None
