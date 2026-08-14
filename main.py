#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ main.py - Ultra-Fast Flashable ROM Maker Engine ⚡
Flashing Script By Mehraan
Zero-Copy Pass-Through | Multi-Core Zstandard (Level 0-22) | Native Multi-Thread STORE Packaging
Powered by gofile_transfer resolver chain and 16MB socket buffer streaming uploader.
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding across Windows/Linux consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.downloader import FastDownloader
from core.extractor import PartitionExtractor
from core.builder import FlashableBuilder
from gofile_transfer.uploader import GoFileUploader


def print_banner(maintainer="Mehraan"):
    print("╔═════════════════════════════════════════════════════════════════════════╗")
    print("║ ⚡ FLASHABLE ROM MAKER ENGINE (ULTRA-FAST NATIVE PIPELINE) ⚡             ║")
    print(f"║ Flashing Script By {maintainer:<12} | Zero-Copy | Multi-Thread Packaging      ║")
    print("╚═════════════════════════════════════════════════════════════════════════╝\n")


def write_github_output(key: str, value: str):
    """Writes key=value to $GITHUB_OUTPUT if running inside GitHub Actions."""
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        try:
            with open(gh_out, "a", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Ultra-Fast Flashable ROM Maker Engine - Flashing Script By Mehraan",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Input sources (URL, local archive file, or local folder)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url", "--imgs-url", "-u",
        dest="url",
        type=str,
        help="Downloadable ROM archive link (SourceForge, Google Drive, MediaFire, Direct HTTP/HTTPS)"
    )
    input_group.add_argument(
        "--file", "-f",
        dest="file",
        type=str,
        help="Path to local archive (.tar.zst, .zip, .7z, .tgz, payload.bin, super.img)"
    )
    input_group.add_argument(
        "--rom-dir", "--imgs-dir", "-d",
        dest="rom_dir",
        type=str,
        help="Path to local directory containing partition images (.img or .img.zst)"
    )

    # Device Metadata
    parser.add_argument("--device", type=str, default="Generic Android Device", help="Device Name (e.g. Infinix GT 20 Pro, POCO F3)")
    parser.add_argument("--codename", type=str, default="generic", help="Device Codename (e.g. X6871, alioth, agate)")
    parser.add_argument("--version", "--firmware", dest="version", type=str, default="v1.0.0-Stable", help="ROM / Firmware Version")
    parser.add_argument("--maintainer", type=str, default="Mehraan", help="Maintainer / Script Author Name")

    # AVB 2.0 / Vbmeta Option
    parser.add_argument(
        "--vbmeta",
        type=str,
        choices=["skip", "disable", "enable"],
        default="skip",
        help="AVB 2.0 / Vbmeta Action: 'skip' (default), 'disable' (dm-verity off), or 'enable'"
    )

    # Compression Configuration: 0 (Raw/Pass-through) to 22 (Max Zstandard)
    parser.add_argument(
        "--zstd-level",
        type=int,
        default=1,
        help="ZSTD compression level (0 = raw/no compression for max speed, 1 = ultra-fast 2.5GB/s, up to 22 max compression)"
    )

    # ZIP Deflate Compression Level: 0 (Store) to 9 (Max Ultra Deflate)
    parser.add_argument(
        "--zip-level",
        type=int,
        default=0,
        help="ZIP compression level (0 = Store mode for max speed, 1-9 = Deflate mode, 9 = Highest compression)"
    )

    # Cloud Upload
    parser.add_argument(
        "--upload",
        type=str,
        choices=["none", "gofile"],
        default="none",
        help="Automatically stream output ZIP to Gofile.io with zero RAM overhead"
    )

    # Output paths
    parser.add_argument("--output", "--out", "-o", dest="output", type=str, default="./output", help="Output ZIP path or directory")
    parser.add_argument("--workspace", type=str, default="./build_workspace", help="Temporary working directory")

    args = parser.parse_args()
    print_banner(args.maintainer)

    print(f"[*] Configuration:")
    print(f"  • Device      : {args.device} ({args.codename})")
    print(f"  • Version     : {args.version}")
    print(f"  • Maintainer  : {args.maintainer}")
    print(f"  • VBmeta Mode : {args.vbmeta.upper()}")
    print(f"  • Zstd Level  : {args.zstd_level} {'(Raw Pass-Through)' if args.zstd_level == 0 else '(Ultra-Fast Multi-Core)' if args.zstd_level == 1 else '(Highest Ultra Compression)' if args.zstd_level >= 20 else ''}")
    print(f"  • ZIP Level   : {args.zip_level} {'(Store mode, Line Rate)' if args.zip_level == 0 else '(Max Deflate Compression)' if args.zip_level == 9 else ''}")
    print(f"  • Auto Upload : {args.upload.upper()}\n")

    work_space = Path(args.workspace).resolve()
    work_space.mkdir(parents=True, exist_ok=True)

    imgs_dir = None

    # Step 1: Ingest input (Download or Extract)
    if args.url:
        archive_file = work_space / "source_archive"
        downloaded = FastDownloader.download(args.url, str(archive_file))
        extracted_dir = work_space / "extracted"
        PartitionExtractor.extract_recursive(str(downloaded), str(extracted_dir))
        imgs_dir = str(extracted_dir)
    elif args.file:
        local_path = Path(args.file).resolve()
        if not local_path.exists():
            sys.exit(f"[!] Error: File does not exist: {local_path}")
        extracted_dir = work_space / "extracted"
        PartitionExtractor.extract_recursive(str(local_path), str(extracted_dir))
        imgs_dir = str(extracted_dir)
    elif args.rom_dir:
        imgs_dir = str(Path(args.rom_dir).resolve())
        if not os.path.isdir(imgs_dir):
            sys.exit(f"[!] Error: Directory does not exist: {imgs_dir}")

    # Step 2: Scan and classify partitions
    print(f"\n[*] Scanning discovered partitions in: {imgs_dir}")
    partitions = PartitionExtractor.scan_partitions(imgs_dir)
    print(f"[+] Total partitions identified: {len(partitions)}")

    if not partitions:
        sys.exit(f"[!] Error: No valid partition images found in '{imgs_dir}'!")

    # Step 3: Determine output path
    output_path = Path(args.output).resolve()
    if output_path.is_dir() or str(args.output).endswith(("/", "\\")) or not str(args.output).endswith(".zip"):
        output_path.mkdir(parents=True, exist_ok=True)
        clean_ver = args.version.replace(" ", "_").replace("/", "-")
        out_zip = str(output_path / f"{clean_ver}-{args.codename}-Flashable-By-Mehraan.zip")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_zip = str(output_path)

    # Step 4: Build Flashable Recovery Package
    final_zip = FlashableBuilder.build(
        partitions=partitions,
        output_zip=out_zip,
        device=args.device,
        firmware=args.version,
        codename=args.codename,
        maintainer=args.maintainer,
        vbmeta_option=args.vbmeta,
        zstd_level=args.zstd_level,
        zip_level=args.zip_level
    )

    print("\n" + "═" * 65)
    print("               BUILD PROCESS COMPLETED IN SECONDS!")
    print(f"  Flashable ZIP : {final_zip}")
    print("═" * 65 + "\n")

    write_github_output("zip_path", final_zip)
    write_github_output("zip_name", Path(final_zip).name)

    # Step 5: Upload to Gofile (if requested)
    if args.upload == "gofile":
        print("[*] Initiating high-speed streaming upload to Gofile.io...")
        uploader = GoFileUploader()
        result = uploader.upload(final_zip)
        if result and result.download_page:
            print("\n" + "═" * 65)
            print("                 GOFILE CLOUD UPLOAD COMPLETE!")
            print(f"  Download Page : {result.download_page}")
            print(f"  File ID       : {result.file_id}")
            print("═" * 65 + "\n")
            write_github_output("download_page", result.download_page)
            write_github_output("file_id", result.file_id)
        else:
            print("[!] Warning: Gofile upload finished without download URL.")


if __name__ == "__main__":
    main()
