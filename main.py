#!/usr/bin/env python3
"""
Flashable-Engine: Master Automation Pipeline
Unified CLI tool for local builds and GitHub Actions CI/CD workflows.

Usage:
  python main.py --url "https://drive.google.com/..." --device "POCO F3" --codename "alioth" --version "16.0.3" --vbmeta disable
  python main.py --rom-dir "./my_extracted_rom" --device "Xiaomi 11T" --codename "agate" --vbmeta skip
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

from core.downloader import UniversalDownloader
from core.extractor import RomExtractor
from core.builder import FlashableBuilder


def main():
    parser = argparse.ArgumentParser(
        description="Flashable-Engine: Advanced Android ROM Flashable Package Builder",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--url", "-u",
        type=str,
        help="Download URL (Google Drive, SourceForge, MediaFire, Mega, Direct HTTP/HTTPS, GitHub Release)"
    )
    group.add_argument(
        "--rom-dir", "-d",
        type=str,
        help="Path to an existing local folder containing ROM images / dumps"
    )
    group.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a local ROM archive or payload.bin file"
    )

    parser.add_argument("--device", type=str, default="POCO F3", help="Target Device Name")
    parser.add_argument("--codename", type=str, default="alioth", help="Device Codename (e.g. alioth, agate, marble)")
    parser.add_argument("--version", type=str, default="v1.0.0-Stable", help="ROM / Firmware Version")
    parser.add_argument("--maintainer", type=str, default="Mehraan", help="Maintainer / Script Author Name")

    parser.add_argument(
        "--vbmeta",
        type=str,
        choices=["disable", "enable", "skip"],
        default="disable",
        help="AVB 2.0 / Vbmeta Action: 'disable' (removes verity/verification), 'enable', or 'skip'"
    )

    parser.add_argument(
        "--compression",
        type=str,
        choices=["zstd", "raw", "erofs"],
        default="zstd",
        help="Partition compression format"
    )

    parser.add_argument(
        "--no-fastboot",
        action="store_true",
        help="Do not include PC Fastboot scripts in the flashable zip"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="Output directory for generated Flashable ZIPs and checksums"
    )

    parser.add_argument(
        "--workspace",
        type=str,
        default="./workspace",
        help="Temporary workspace directory for downloads and extraction"
    )

    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("       FLASHABLE-ENGINE: CLOUD & LOCAL BUILD PIPELINE")
    print("                Flashing Script By " + args.maintainer)
    print("=" * 65)
    print(f" • Device      : {args.device} ({args.codename})")
    print(f" • Version     : {args.version}")
    print(f" • VBmeta Mode : {args.vbmeta.upper()}")
    print(f" • Compression : {args.compression.upper()}")
    print(f" • Fastboot    : {'Enabled' if not args.no_fastboot else 'Disabled'}")
    print("=" * 65 + "\n")

    workspace = Path(args.workspace).resolve()
    downloads_dir = workspace / "downloads"
    output_dir = Path(args.output).resolve()

    # Step 1: Obtain ROM Input
    extractor = RomExtractor(workspace_dir=str(workspace / "extracted"))

    if args.url:
        downloader = UniversalDownloader(output_dir=str(downloads_dir))
        downloaded_file = downloader.download(args.url)
        staged_partitions_dir = extractor.extract_package(downloaded_file)
    elif args.file:
        staged_partitions_dir = extractor.extract_package(Path(args.file))
    elif args.rom_dir:
        staged_partitions_dir = extractor.extract_package(Path(args.rom_dir))
    else:
        print("[ERROR] No input specified.")
        sys.exit(1)

    # Step 2: Build Flashable ZIP
    builder = FlashableBuilder(
        device_name=args.device,
        codename=args.codename,
        version=args.version,
        maintainer=args.maintainer,
        vbmeta_option=args.vbmeta,
        compression=args.compression,
        include_fastboot=(not args.no_fastboot),
        output_dir=str(output_dir)
    )

    final_zip = builder.build_flashable_zip(staged_partitions_dir)

    print("\n" + "═" * 65)
    print("               BUILD PROCESS COMPLETED!")
    print(f"  Flashable ZIP : {final_zip}")
    print("═" * 65 + "\n")

    # Set GitHub Actions output variable if in CI
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output and os.path.exists(github_output):
        with open(github_output, "a") as f:
            f.write(f"zip_path={final_zip}\n")
            f.write(f"zip_name={final_zip.name}\n")


if __name__ == "__main__":
    main()
