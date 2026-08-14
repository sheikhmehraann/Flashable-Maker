#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ gofile_upload.py - Ultra-Fast Streaming Gofile.io Uploader CLI ⚡
Zero-RAM streaming uploader for large ROM files (10GB+).
Prevents memory exhaustion by streaming directly from disk to socket.
"""

import os
import sys
import json
import argparse
import subprocess
import urllib.request
from typing import Optional, Dict, Any

GOFILE_SERVERS_API = "https://api.gofile.io/servers"
DEFAULT_FALLBACK_SERVERS = ["store1", "store2", "store3"]

def get_optimal_server(token: Optional[str] = None) -> str:
    """Query Gofile API to retrieve an active, online upload server."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(GOFILE_SERVERS_API, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok":
                    server_data = data.get("data", {})
                    servers = server_data.get("servers", [])
                    if isinstance(servers, list) and servers:
                        online = [
                            s.get("name") for s in servers
                            if isinstance(s, dict) and s.get("status") == "online" and s.get("name")
                        ]
                        if online:
                            return online[0]
                        first = servers[0].get("name") if isinstance(servers[0], dict) else None
                        if first:
                            return first
                    srv_str = server_data.get("server")
                    if srv_str and isinstance(srv_str, str):
                        return srv_str
    except Exception as e:
        sys.stderr.write(f"[!] Warning: Gofile server resolution failed ({e}). Using fallback.\n")

    return "store1"

def upload_streaming_curl(filepath: str, server: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Streams file directly from disk via native curl with zero RAM overhead."""
    upload_url = f"https://{server}.gofile.io/contents/uploadfile"
    cmd = ["curl", "-sSL", "-X", "POST", upload_url, "-F", f"file=@{filepath}"]
    if token:
        cmd.extend(["-F", f"token={token}", "-H", f"Authorization: Bearer {token}"])

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"curl upload failed with code {res.returncode}: {res.stderr}")

    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected response from Gofile: {res.stdout}")

def write_github_output(key: str, value: str):
    """Writes key=value to $GITHUB_OUTPUT if running inside GitHub Actions."""
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        try:
            with open(gh_out, "a", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            print(f"[+] Output written to $GITHUB_OUTPUT: {key}={value}")
        except Exception as e:
            sys.stderr.write(f"[!] Warning: Could not write to $GITHUB_OUTPUT: {e}\n")

def main():
    parser = argparse.ArgumentParser(description="Streaming Gofile Uploader")
    parser.add_argument("filepath", help="Path to file to upload")
    parser.add_argument("--token", default=None, help="Gofile API token (optional)")
    args = parser.parse_args()

    if not os.path.isfile(args.filepath):
        sys.stderr.write(f"[!] Error: File does not exist: '{args.filepath}'\n")
        sys.exit(1)

    file_size_mb = os.path.getsize(args.filepath) / (1024 * 1024)
    print(f"[*] Resolving optimal Gofile upload server...")
    server = get_optimal_server(token=args.token)
    print(f"[+] Upload target: https://{server}.gofile.io/contents/uploadfile")
    print(f"[*] Streaming '{args.filepath}' ({file_size_mb:.2f} MB)...")

    try:
        res = upload_streaming_curl(args.filepath, server, token=args.token)
    except Exception as e:
        sys.stderr.write(f"[!] Upload error: {e}\n")
        sys.exit(1)

    if res.get("status") == "ok":
        download_page = res.get("data", {}).get("downloadPage")
        file_id = res.get("data", {}).get("fileId")
        print(f"\n[🚀 SUCCESS] Upload completed successfully!")
        print(f"   Download Page: {download_page}")
        print(f"   File ID      : {file_id}\n")

        if download_page:
            write_github_output("download_page", download_page)
        if file_id:
            write_github_output("file_id", file_id)
    else:
        sys.stderr.write(f"[!] Upload returned non-OK status: {json.dumps(res, indent=2)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
