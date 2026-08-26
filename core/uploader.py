#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ core/uploader.py - Flashable-Engine Cloud Uploader Module ⚡
Seamlessly uploads generated flashable packages to Gofile.io or Transfer.sh.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict

from gofile_transfer.uploader import GoFileUploader, GoFileResult


class CloudUploader:
    """Handles automatic upload to high-speed hosting providers."""

    @staticmethod
    def upload_gofile(file_path: Path, token: Optional[str] = None) -> Optional[str]:
        """Uploads file to Gofile.io and returns the public download link."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            print(f"[GOFILE] Error: File {file_path} does not exist.")
            return None

        print(f"\n[GOFILE] Uploading {file_path.name} ({file_path.stat().st_size / (1024*1024):.2f} MB) to Gofile.io...")

        token_to_use = token or os.environ.get("GOFILE_TOKEN", "").strip() or None

        try:
            uploader = GoFileUploader(token=token_to_use)
            result: GoFileResult = uploader.upload(str(file_path))
            if result and result.download_page:
                print(f"[GOFILE] ✅ Upload Successful! Download Page: {result.download_page}")
                return result.download_page
        except Exception as e:
            print(f"[GOFILE] Upload failed: {e}")

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
        curl_bin = "curl.exe" if shutil.which("curl.exe") else ("curl" if shutil.which("curl") else None)
        if curl_bin:
            try:
                cmd = [curl_bin, "-sSL", "--upload-file", str(file_path), f"https://transfer.sh/{file_path.name}"]
                link = subprocess.check_output(cmd, timeout=300).decode("utf-8").strip()
                print(f"[TRANSFER.SH] ✅ Upload Successful! Download Link: {link}")
                return link
            except Exception as e:
                print(f"[TRANSFER.SH] Upload error: {e}")
        return None
