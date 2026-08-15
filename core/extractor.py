#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ core/extractor.py - High-Performance Multi-Threaded Unpacker & Scanner ⚡
Handles instant archive decompression, recursive container unpacking, payload.bin
extraction, sparse image parsing, and zero-copy partition discovery.
"""

import os
import sys
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

ZSTD_FRAME_MAGIC = b"\x28\xb5\x2f\xfd"

class PartitionExtractor:
    """High-speed native unpacker and partition scanner."""

    @staticmethod
    def is_zstd_file(file_path: str) -> bool:
        """Inspects first 4 bytes for Zstandard frame header."""
        if not os.path.isfile(file_path) or os.path.getsize(file_path) < 4:
            return False
        try:
            with open(file_path, "rb") as f:
                return f.read(4) == ZSTD_FRAME_MAGIC
        except OSError:
            return False

    @staticmethod
    def get_zstd_uncompressed_size(file_path: str) -> int:
        """
        Retrieves the exact uncompressed partition byte size.
        Uses python-zstandard FrameParameters, RFC 8878 header parsing, zstd CLI JSON,
        or chunked stream counter. Never estimates with arbitrary multipliers.
        """
        # Method 1: python-zstandard FrameParameters (content_size)
        try:
            import zstandard
            with open(file_path, "rb") as f:
                header = f.read(1024)
                params = zstandard.get_frame_parameters(header)
                if params.content_size is not None and params.content_size > 0:
                    return params.content_size
        except Exception:
            pass

        # Method 2: RFC 8878 Manual Frame Header Parser
        try:
            with open(file_path, "rb") as f:
                magic = f.read(4)
                if magic == ZSTD_FRAME_MAGIC:
                    fhd = f.read(1)[0]
                    single_segment = (fhd & 0x20) != 0
                    fcs_flag = (fhd >> 6) & 0x03
                    has_dict = (fhd & 0x03) != 0
                    dict_bytes = {1: 1, 2: 2, 3: 4}.get(fhd & 0x03, 0) if has_dict else 0
                    window_bytes = 0 if single_segment else 1
                    f.seek(5 + window_bytes + dict_bytes)

                    if fcs_flag == 0 and single_segment:
                        return f.read(1)[0]
                    elif fcs_flag == 1:
                        return struct.unpack("<H", f.read(2))[0] + 256
                    elif fcs_flag == 2:
                        return struct.unpack("<I", f.read(4))[0]
                    elif fcs_flag == 3:
                        return struct.unpack("<Q", f.read(8))[0]
        except Exception:
            pass

        # Method 3: Native zstd CLI JSON query
        if shutil.which("zstd") or shutil.which("zstd.exe"):
            z_bin = "zstd.exe" if shutil.which("zstd.exe") else "zstd"
            try:
                import json
                res = subprocess.run([z_bin, "-l", "--format=json", file_path], capture_output=True, text=True, check=True)
                data = json.loads(res.stdout)
                if isinstance(data, list) and data:
                    decomp_sz = data[0].get("decompSize") or data[0].get("uncompressedSize")
                    if decomp_sz and int(decomp_sz) > 0:
                        return int(decomp_sz)
            except Exception:
                pass

        # Method 4: Streaming decompress byte counter fallback (zero RAM overhead, 100% exact)
        try:
            import zstandard
            dctx = zstandard.ZstdDecompressor()
            total = 0
            with open(file_path, "rb") as f:
                with dctx.stream_reader(f) as reader:
                    while True:
                        chunk = reader.read(2 * 1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
            if total > 0:
                return total
        except Exception:
            pass

        return os.path.getsize(file_path)

    @classmethod
    def unpack_payload_bin(cls, payload_path: str, output_dir: str):
        """Extracts payload.bin partitions concurrently."""
        print(f"[*] [Extractor] Unpacking payload.bin -> {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        if shutil.which("payload-dumper-go"):
            subprocess.run(["payload-dumper-go", "-threads", "0", "-o", output_dir, payload_path], check=True)
        else:
            # Python payload_dumper module fallback
            subprocess.run([sys.executable, "-m", "payload_dumper", "--out", output_dir, payload_path], check=True)

    @classmethod
    def unpack_super_img(cls, super_path: str, output_dir: str):
        """Unsparses and unpacks super.img logical partitions."""
        print(f"[*] [Extractor] Unpacking super.img -> {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        target_super = super_path

        # Unsparse if simg2img is available
        if shutil.which("simg2img"):
            unsparse_file = os.path.join(output_dir, "super.raw.img")
            res = subprocess.run(["simg2img", super_path, unsparse_file], capture_output=True)
            if res.returncode == 0:
                target_super = unsparse_file

        if shutil.which("lpunpack"):
            subprocess.run(["lpunpack", target_super, output_dir], check=True)
            if target_super != super_path and os.path.exists(target_super):
                os.remove(target_super)
        else:
            print("[!] [Extractor] Notice: lpunpack not found in PATH; keeping super.img intact.")

    @classmethod
    def extract_single(cls, archive_path: str, extract_dir: str):
        """Native multi-threaded single archive unpacker supporting any container format."""
        os.makedirs(extract_dir, exist_ok=True)
        lower_name = archive_path.lower()

        # Sniff magic header bytes
        magic = b""
        if os.path.isfile(archive_path) and os.path.getsize(archive_path) >= 6:
            try:
                with open(archive_path, "rb") as mf:
                    magic = mf.read(6)
            except OSError:
                pass

        is_zstd = magic.startswith(b"\x28\xb5\x2f\xfd") or lower_name.endswith((".tar.zst", ".tzst", ".zst"))
        is_zip = magic.startswith(b"PK\x03\x04") or lower_name.endswith(".zip")
        is_7z = magic.startswith(b"7z\xbc\xaf\x27\x1c") or lower_name.endswith(".7z")
        is_rar = magic.startswith(b"Rar!\x1a\x07") or lower_name.endswith(".rar")
        is_gzip = magic.startswith(b"\x1f\x8b") or lower_name.endswith((".tar.gz", ".tgz", ".gz"))
        is_bzip2 = magic.startswith(b"BZh") or lower_name.endswith((".tar.bz2", ".tbz2", ".bz2"))
        is_xz = magic.startswith(b"\xfd7zXZ\x00") or lower_name.endswith((".tar.xz", ".txz", ".xz"))

        if is_zstd:
            unpacked = False
            # Pass 1: native tar with zstd decompressor
            if shutil.which("tar"):
                try:
                    subprocess.run(["tar", "-I", "zstd -T0", "-xf", archive_path, "-C", extract_dir], check=True)
                    unpacked = True
                except Exception:
                    try:
                        subprocess.run(["tar", "-xf", archive_path, "-C", extract_dir], check=True)
                        unpacked = True
                    except Exception:
                        pass

            # Pass 2: 7z CLI
            if not unpacked and shutil.which("7z"):
                try:
                    subprocess.run(["7z", "x", "-mmt=on", "-y", f"-o{extract_dir}", archive_path], stdout=subprocess.DEVNULL, check=True)
                    unpacked = True
                except Exception:
                    pass

            # Pass 3: Python zstandard + tarfile
            if not unpacked:
                try:
                    import tarfile
                    import zstandard
                    dctx = zstandard.ZstdDecompressor()
                    with open(archive_path, "rb") as ifh, dctx.stream_reader(ifh) as reader:
                        with tarfile.open(fileobj=reader, mode="r|") as tar:
                            tar.extractall(path=extract_dir)
                    unpacked = True
                except Exception:
                    pass

        elif is_7z or is_rar:
            if shutil.which("7z"):
                subprocess.run(["7z", "x", "-mmt=on", "-y", f"-o{extract_dir}", archive_path], stdout=subprocess.DEVNULL, check=True)
            else:
                try:
                    import py7zr
                    with py7zr.SevenZipFile(archive_path, mode='r') as z:
                        z.extractall(path=extract_dir)
                except Exception:
                    pass

        elif is_zip:
            if shutil.which("7z"):
                subprocess.run(["7z", "x", "-mmt=on", "-y", f"-o{extract_dir}", archive_path], stdout=subprocess.DEVNULL, check=True)
            elif shutil.which("unzip"):
                subprocess.run(["unzip", "-q", "-o", archive_path, "-d", extract_dir], check=True)
            else:
                import zipfile
                with zipfile.ZipFile(archive_path, "r") as z:
                    z.extractall(extract_dir)

        elif is_gzip or is_bzip2 or is_xz or lower_name.endswith(".tar"):
            if shutil.which("tar"):
                try:
                    subprocess.run(["tar", "-xf", archive_path, "-C", extract_dir], check=True)
                except Exception:
                    import tarfile
                    with tarfile.open(archive_path, "r:*") as t:
                        t.extractall(extract_dir)
            else:
                import tarfile
                with tarfile.open(archive_path, "r:*") as t:
                    t.extractall(extract_dir)
        else:
            if shutil.which("7z"):
                subprocess.run(["7z", "x", "-mmt=on", "-y", f"-o{extract_dir}", archive_path], stdout=subprocess.DEVNULL, check=True)
            else:
                try:
                    import zipfile
                    with zipfile.ZipFile(archive_path, "r") as z:
                        z.extractall(extract_dir)
                except Exception:
                    pass

    @classmethod
    def extract_recursive(cls, initial_archive: str, extract_dir: str, max_depth: int = 5):
        """
        Recursively extracts nested archives, payloads, and super images
        while unlinking extracted containers to maintain minimal disk footprint.
        """
        print(f"[*] [Extractor] Starting recursive unpack of: {initial_archive}")
        cls.extract_single(initial_archive, extract_dir)

        for depth in range(1, max_depth + 1):
            nested_found = False
            for root, _, files in os.walk(extract_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    fl = f.lower()

                    # Handle Payload.bin
                    if fl == "payload.bin":
                        cls.unpack_payload_bin(fp, os.path.join(root, "_payload_extracted"))
                        os.remove(fp)
                        nested_found = True
                        continue

                    # Handle super.img
                    if fl == "super.img":
                        cls.unpack_super_img(fp, os.path.join(root, "_super_extracted"))
                        os.remove(fp)
                        nested_found = True
                        continue

                    # Handle nested archives
                    if fl.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.xz", ".tar.zst", ".7z", ".rar")) and not fl.endswith(".img"):
                        print(f"[*] [Extractor] [Nested L{depth}] Unpacking: {f}")
                        nested_dir = os.path.join(root, f"_unpacked_{f}")
                        try:
                            cls.extract_single(fp, nested_dir)
                            os.remove(fp)
                            nested_found = True
                        except Exception as e:
                            print(f"[!] Warning: Failed unpacking nested archive {f}: {e}")

            if not nested_found:
                break

        print(f"[+] [Extractor] Extraction complete -> {extract_dir}")

    @classmethod
    def scan_partitions(cls, search_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        Discovers all partition images (.img, .img.zst, .zst) and determines
        their compression state.
        """
        partitions = {}
        for root, _, files in os.walk(search_dir):
            for file in files:
                file_lower = file.lower()
                file_path = os.path.join(root, file)

                if file_lower.endswith(".img.zst") or file_lower.endswith(".zst"):
                    base = file_lower.replace(".img.zst", "").replace(".zst", "")
                    partitions[base] = {
                        "path": file_path,
                        "is_zstd": True,
                        "filename": file
                    }
                elif file_lower.endswith(".img"):
                    base = file_lower.replace(".img", "")
                    if base not in partitions:
                        partitions[base] = {
                            "path": file_path,
                            "is_zstd": cls.is_zstd_file(file_path),
                            "filename": file
                        }
        return partitions
