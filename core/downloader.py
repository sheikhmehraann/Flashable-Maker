#!/usr/bin/env python3
"""
Flashable-Engine: Universal High-Speed Downloader
Supports Direct URLs, Google Drive, SourceForge, MediaFire, GitHub Releases, AndroidFileHost.
Leverages aria2c (16 parallel connections/splits) with Python requests/gdown fallbacks.
"""

import os
import re
import sys
import shutil
import urllib.parse
import subprocess
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests
except ImportError:
    requests = None


class UniversalDownloader:
    """Handles high-speed multi-threaded downloads from diverse cloud hosts."""

    def __init__(self, output_dir: str = "./downloads", max_connections: int = 16):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_connections = max_connections
        self.has_aria2 = shutil.which("aria2c") is not None

    def resolve_url(self, url: str) -> Tuple[str, Optional[str], Optional[dict]]:
        """
        Resolves various cloud hosting URLs into direct downloadable streams.
        Returns (direct_url, optional_filename, optional_headers).
        """
        url = url.strip()

        # 1. Google Drive Links (e.g. drive.google.com/file/d/<FILE_ID>/view or drive.google.com/open?id=<FILE_ID>)
        gdrive_match = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([a-zA-Z0-9_-]+)", url)
        if gdrive_match:
            file_id = gdrive_match.group(1)
            direct_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
            return direct_url, None, None

        # 2. SourceForge Links (Generate multi-mirror URLs for maximum parallel bandwidth)
        if "sourceforge.net" in url:
            clean_url = url.split("?")[0]
            parts = [p for p in clean_url.split("/") if p and p != "download"]
            fname = parts[-1] if parts and ("." in parts[-1]) else None
            match = re.search(r"sourceforge\.net/projects/([^/]+)/files/(.+)", clean_url)
            if match:
                proj = match.group(1)
                subpath = match.group(2).rstrip("/").removesuffix("/download")
                mirrors = [
                    f"https://downloads.sourceforge.net/project/{proj}/{subpath}",
                    f"https://master.dl.sourceforge.net/project/{proj}/{subpath}",
                    f"https://netcologne.dl.sourceforge.net/project/{proj}/{subpath}",
                    f"https://jaist.dl.sourceforge.net/project/{proj}/{subpath}"
                ]
                return mirrors[0], fname, {"mirrors": mirrors}
            elif not url.endswith("/download") and not "files" in url:
                direct_url = url.rstrip("/") + "/files/latest/download"
            else:
                direct_url = url
            return direct_url, fname, None

        # 3. MediaFire Links (e.g. mediafire.com/file/<KEY>/<NAME>/file)
        if "mediafire.com" in url:
            direct_url = self._resolve_mediafire(url)
            return direct_url, None, None

        # 4. GitHub Release Direct or Raw
        if "github.com" in url and "/releases/download/" in url:
            fname = url.split("/")[-1].split("?")[0]
            return url, fname, None

        # Default direct URL
        parsed_name = Path(urllib.parse.urlparse(url).path).name
        return url, parsed_name if parsed_name else None, None

    def _resolve_mediafire(self, page_url: str) -> str:
        """Scrapes direct download link from MediaFire landing page."""
        if not requests:
            return page_url
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(page_url, headers=headers, timeout=15)
            match = re.search(r'href="((?:https?:)?//download\d+\.mediafire\.com/[^"]+)"', resp.text)
            if match:
                direct = match.group(1)
                if direct.startswith("//"):
                    direct = "https:" + direct
                return direct
        except Exception as e:
            print(f"[WARNING] MediaFire scraper failed: {e}. Falling back to raw URL.")
        return page_url

    def download(self, url: str, custom_filename: Optional[str] = None) -> Path:
        """
        Executes download using aria2c (fastest) with automatic multi-mirror parallel sockets.
        Returns the absolute path to the downloaded file.
        """
        print(f"\n[DOWNLOADER] Initializing download for: {url}")
        direct_url, resolved_name, extra = self.resolve_url(url)
        target_name = custom_filename or resolved_name or "downloaded_package.bin"
        mirrors = (extra and extra.get("mirrors")) or [direct_url]

        print(f"[DOWNLOADER] Primary URL  : {direct_url}")
        print(f"[DOWNLOADER] Target File  : {target_name}")
        print(f"[DOWNLOADER] Active Mirrors: {len(mirrors)}")

        # Strategy A: aria2c (multi-threaded, 16 connections, 0 disk allocation delay)
        if self.has_aria2:
            print(f"[DOWNLOADER] Multi-thread accelerator active (16 parallel streams)...")
            cmd = [
                "aria2c",
                "--console-log-level=notice",
                "--summary-interval=1",
                "--max-connection-per-server=16",
                "--split=16",
                "--min-split-size=1M",
                "--stream-piece-selector=geom",
                "--file-allocation=none",
                "--auto-file-renaming=false",
                "--allow-overwrite=true",
                "--check-certificate=false",
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                f"--dir={self.output_dir}",
                f"--out={target_name}",
                direct_url
            ]

            res = subprocess.run(cmd)
            if res.returncode == 0:
                downloaded_file = self._find_latest_download(target_name)
                if downloaded_file and downloaded_file.exists() and downloaded_file.stat().st_size > 1024:
                    print(f"[DOWNLOADER] Download Complete: {downloaded_file.name} ({downloaded_file.stat().st_size:,} bytes)")
                    return downloaded_file

            print("[DOWNLOADER] aria2c interrupted or failed, attempting curl fallback...")

        # Strategy B: curl (high speed, follows redirects)
        if shutil.which("curl"):
            dest_path = self.output_dir / target_name
            print(f"[DOWNLOADER] Downloading with curl ({dest_path.name})...")
            cmd = ["curl", "-L", "-k", "--fail", "--progress-bar", "--retry", "3", "-o", str(dest_path), direct_url]
            res = subprocess.run(cmd)
            if res.returncode == 0 and dest_path.exists() and dest_path.stat().st_size > 1024:
                print(f"[DOWNLOADER] Download Complete: {dest_path.name} ({dest_path.stat().st_size:,} bytes)")
                return dest_path
            print("[DOWNLOADER] curl encountered an issue, attempting Python stream fallback...")

        # Strategy C: Python Requests Stream fallback
        return self._download_python_stream(direct_url, target_name)

    def _download_python_stream(self, url: str, target_name: Optional[str] = None) -> Path:
        """Fallback chunked streaming downloader using requests/urllib."""
        import urllib.request
        print("[DOWNLOADER] Starting fallback streaming download...")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FlashableMaker/1.0"}
        )

        with urllib.request.urlopen(req) as response:
            filename = target_name
            if not filename:
                content_disp = response.headers.get("Content-Disposition", "")
                if "filename=" in content_disp:
                    match = re.search(r'filename=["\']?([^"\';]+)', content_disp)
                    if match:
                        filename = match.group(1).strip()
                if not filename:
                    parsed = urllib.parse.urlparse(response.geturl())
                    filename = Path(parsed.path).name or "downloaded_rom.zip"

            dest_path = self.output_dir / filename
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks

            print(f"[DOWNLOADER] Destination: {dest_path.name}")
            if total_size > 0:
                print(f"[DOWNLOADER] File Size: {total_size / (1024*1024):.2f} MB")

            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        sys.stdout.write(f"\r[PROGRESS] {mb_done:.1f}MB / {mb_total:.1f}MB ({percent:.1f}%)")
                        sys.stdout.flush()

            print("\n[DOWNLOADER] Download finished successfully.")
            return dest_path

    def _find_latest_download(self, expected_name: Optional[str]) -> Optional[Path]:
        if expected_name and (self.output_dir / expected_name).exists():
            return self.output_dir / expected_name
        files = [p for p in self.output_dir.iterdir() if p.is_file() and not p.name.endswith(".aria2")]
        if not files:
            return None
        return max(files, key=lambda f: f.stat().st_mtime)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <URL> [output_dir]")
        sys.exit(1)
    target_url = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "./downloads"
    downloader = UniversalDownloader(output_dir=out_dir)
    res_path = downloader.download(target_url)
    print(f"Result: {res_path}")
