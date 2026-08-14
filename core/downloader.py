#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ core/downloader.py - Ultra-Fast Multi-Connection Downloader ⚡
High-throughput accelerated file fetcher utilizing aria2c with zero-allocation,
SourceForge CDN mirror resolution, and curl streaming fallbacks.
"""

import os
import sys
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional


class FastDownloader:
    """Accelerated downloader with 16-connection pipeline and stream validation."""

    @classmethod
    def resolve_url(cls, url: str) -> str:
        """Converts SourceForge web project links into direct CDN URLs."""
        if "sourceforge.net" in url:
            clean_url = url.split("?")[0]
            match = re.search(r"sourceforge\.net/projects/([^/]+)/files/(.+)", clean_url)
            if match:
                proj = match.group(1)
                subpath = match.group(2).rstrip("/").removesuffix("/download")
                return f"https://downloads.sourceforge.net/project/{proj}/{subpath}"
        return url

    @staticmethod
    def is_html_response(file_path: str) -> bool:
        """Inspects file head to ensure payload is not an HTML error/login page."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
        with open(file_path, 'rb') as f:
            header = f.read(256).lower()
            return b'<!doctype html' in header or b'<html' in header or b'<head' in header

    @classmethod
    def download(cls, url: str, output_path: str, max_connections: int = 16) -> str:
        """
        Downloads a remote archive using aria2c multi-connection acceleration.
        Falls back to curl or buffered streaming urllib.
        """
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(output_path)

        direct_url = cls.resolve_url(url)
        print(f"[*] [Downloader] Fetching source archive: {direct_url}")

        aria2_bin = shutil.which("aria2c")
        downloaded = False

        if aria2_bin:
            print(f"[+] [Downloader] Spawning aria2c ({max_connections} parallel streams, --file-allocation=none)...")
            cmd = [
                aria2_bin,
                f"-x{max_connections}",
                f"-s{max_connections}",
                f"-j{max_connections}",
                "-k1M",
                "--file-allocation=none",
                "--allow-overwrite=true",
                "--auto-file-renaming=false",
                "--summary-interval=1",
                "--check-certificate=false",
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                "-d", output_dir,
                "-o", filename,
                direct_url
            ]
            res = subprocess.run(cmd)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                downloaded = True

        if not downloaded:
            print("[!] [Downloader] Trying high-speed curl fallback...")
            curl_bin = shutil.which("curl")
            if curl_bin:
                cmd = [
                    curl_bin, "-L", "-k", "--fail", "--retry", "3",
                    "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "-o", output_path, direct_url
                ]
                res = subprocess.run(cmd)
                if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                    downloaded = True

        if not downloaded:
            print("[!] [Downloader] Falling back to 4MB chunked HTTP streaming...")
            req = urllib.request.Request(
                direct_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp, open(output_path, "wb") as out_f:
                chunk_size = 4 * 1024 * 1024  # 4MB buffer
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                downloaded = True

        if cls.is_html_response(output_path):
            raise ValueError(
                f"Downloaded file '{output_path}' contains HTML web content instead of a binary ROM archive. "
                "Ensure you provide a direct binary link."
            )

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[+] [Downloader] Download completed: {output_path} ({file_size_mb:.2f} MB)")
        return output_path
