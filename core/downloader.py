#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ core/downloader.py - Ultra-Fast Multi-Connection Downloader ⚡
Integrates gofile_transfer resolver chain and 16-connection aria2c / RAM disk engine.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

from gofile_transfer.resolvers.factory import ResolverFactory
from gofile_transfer.downloader import ParallelDownloader


class FastDownloader:
    """Accelerated downloader powered by gofile_transfer engine."""

    @classmethod
    def download(cls, url: str, output_path: str, max_connections: int = 16) -> str:
        """
        Resolves link (SourceForge, Google Drive, MediaFire, Direct) and downloads
        with 16-connection aria2c acceleration.
        """
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(output_path)

        print(f"[*] [Downloader] Resolving source link: {url}")
        factory = ResolverFactory()
        resolved = factory.resolve(url)
        print(f"[+] [Downloader] Resolved Target : {resolved.direct_url}")
        print(f"[+] [Downloader] Remote Filename : {resolved.filename}")
        if resolved.file_size:
            print(f"[+] [Downloader] Payload Size    : {resolved.file_size / (1024*1024):.2f} MB")

        # Preserve remote extension if custom filename lacks one
        if resolved.filename and "." in resolved.filename and "." not in filename:
            remote_ext = "".join(Path(resolved.filename).suffixes)
            filename = f"{filename}{remote_ext}"
        elif resolved.filename and not filename:
            filename = resolved.filename

        downloader = ParallelDownloader(num_connections=max_connections)
        downloaded_file = downloader.download(
            resolved=resolved,
            output_dir=output_dir,
            custom_filename=filename
        )

        if not os.path.exists(downloaded_file) or os.path.getsize(downloaded_file) < 1024:
            raise RuntimeError(f"Download failed or output file is empty: {downloaded_file}")

        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        print(f"[+] [Downloader] Download completed: {downloaded_file} ({file_size_mb:.2f} MB)")
        return downloaded_file
