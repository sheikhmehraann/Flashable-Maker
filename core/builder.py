#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ core/builder.py - Ultra-Fast Flashable Recovery Package Builder ⚡
Implements zero-copy pass-through, multi-process Zstandard parallel compression,
dynamic updater script generation, and native multi-threaded STORE-mode ZIP packaging.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any

from .extractor import PartitionExtractor

SUPER_PARTITIONS = {
    "system", "vendor", "product", "system_dlkm", "system_ext",
    "vendor_dlkm", "odm_dlkm", "odm", "mi_ext"
}
SUPER_TR_PARTITIONS = {
    "tr_carrier", "tr_company", "tr_mi", "tr_overlayfs",
    "tr_preload", "tr_product", "tr_region", "tr_theme",
    "tr_manifest", "tr_misc"
}
SYSTEMS = {
    "boot", "dtbo", "init_boot", "vendor_boot",
    "vbmeta", "vbmeta_system", "vbmeta_vendor", "recovery"
}
FIRMWARES = {
    "apusys", "cam_vpu1", "cam_vpu2", "cam_vpu3", "ccu", "connsys_bt",
    "dpm", "gpueb", "gz", "lk", "logo", "mcf_ota", "mcupm", "md1img",
    "mvpu_algo", "pi_img", "preloader_raw", "scp", "spmfw", "sspm",
    "tee", "tkv", "vcp"
}

def fast_stage_file(src: str, dst: str):
    """Zero-copy staging via filesystem hardlink or atomic copy."""
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except (OSError, AttributeError):
        shutil.copy2(src, dst)

def compress_single_image_worker(task: Tuple[str, str, str, int, int]) -> Tuple[str, int]:
    """
    Worker task: Compresses a raw .img partition using multi-threaded zstd (Level 0-22).
    """
    name, in_file, out_file, level, raw_size = task
    
    if level <= 0:
        # Level 0 = Ultra-Fast Instant Framing (--fast=10 delivers >3.5 GB/s throughput)
        cmd = ["zstd", "--fast=10", "-T0", "-f", "-q", in_file, "-o", out_file]
    elif level >= 20:
        # Ultra compression mode
        cmd = ["zstd", f"-{level}", "--ultra", "-T0", "-f", "-q", in_file, "-o", out_file]
    else:
        cmd = ["zstd", f"-{level}", "-T0", "-f", "-q", in_file, "-o", out_file]

    if shutil.which("zstd"):
        subprocess.run(cmd, check=True)
    else:
        import zstandard
        c_level = max(1, min(level, 22))
        cctx = zstandard.ZstdCompressor(level=c_level, threads=-1)
        with open(in_file, "rb") as ifh, open(out_file, "wb") as ofh:
            cctx.copy_stream(ifh, ofh)
    return name, raw_size

class FlashableBuilder:
    """Orchestrates high-speed recovery package synthesis."""

    @classmethod
    def generate_update_binary(
        cls,
        device: str,
        firmware: str,
        codename: str,
        super_specs: List[Tuple[str, int]],
        system_imgs: List[str],
        firmware_imgs: List[str],
        tr_specs: List[Tuple[str, int]],
        maintainer: str = "Mehraan",
        vbmeta_option: str = "skip"
    ) -> str:
        """Generates dynamic updater-binary shell script."""
        sb = [
            "#!/sbin/sh",
            "OUTFD=/proc/self/fd/$2",
            'ZIPFILE="$3"',
            "",
            "ui_print() {",
            '    printf \'ui_print %s\\nui_print\\n\' "$1" >>"$OUTFD"',
            "}",
            "",
            "flash_partition() {",
            '    src="$1"; dest="$2"; msg="$3"',
            '    if [ -n "$msg" ]; then ui_print "$msg"; fi',
            '    unzip -p "$ZIPFILE" "$src" >"$dest" || {',
            '        ui_print "Error: Failed to flash $src to $dest"',
            '        exit 1',
            '    }',
            "}",
            "",
            "flash_partition_zstd() {",
            '    src="$1"; dest="$2"',
            '    partition_name=$(echo "$dest" | cut -d \'/\' -f 5)',
            '    ui_print "- Flashing partition $partition_name"',
            '    unzip -p "$ZIPFILE" "$src" | /tmp/META-INF/zstd -c -d >"$dest" || {',
            '        ui_print "Error: Failed to flash compressed $src to $dest"',
            '        exit 1',
            '    }',
            "}",
            "",
            "flash_firmware_both_slots() {",
            '    img_file="$1"; base_name="$2"',
            '    flash_partition "$img_file" "/dev/block/by-name/${base_name}_a" "- Flashing ${base_name} to both slots"',
            '    flash_partition "$img_file" "/dev/block/by-name/${base_name}_b" ""',
            "}",
            "",
            "getVolumeKey() {",
            '    ui_print "- Press [+] for Yes and [-] for No"',
            "    while true; do",
            '        keyInfo=$(getevent -qlc 1 | grep KEY_VOLUME)',
            '        [ -z "$keyInfo" ] && continue',
            '        isUpKey=$(printf \'%s\\n\' "$keyInfo" | grep KEY_VOLUMEUP)',
            '        if [ -n "$isUpKey" ]; then return 0; else return 1; fi',
            "    done",
            "}",
            "",
            "checkDevice() {",
            '    myDevice=$(getprop ro.product.device)',
            '    [ -z "$myDevice" ] && myDevice=$(getprop ro.build.product)',
            '    [ -z "$myDevice" ] && myDevice=$(getprop ro.product.name)',
            f'    romDevice="{codename}"',
            '    if [ -z "$(echo "$myDevice" | grep -i "$romDevice")" ]; then',
            '        ui_print "- Warning: Target mismatch! Current: $myDevice, Expected: $romDevice"',
            '        ui_print "- Do you wish to continue flashing?"',
            '        if ! getVolumeKey; then ui_print "- Flashing aborted."; exit 1; fi',
            '    fi',
            "}",
            "",
            "checkExit() {",
            '    status=$?',
            '    if [ "$status" -ne 0 ]; then',
            '        ui_print "Error: Dynamic partition operation failed. Please flash stock super.img first."',
            '        exit 1',
            '    fi',
            "}",
            "",
            "unmountPartitions() {",
            '    umount /system /system_root /vendor /product /system_ext /vendor_dlkm /odm_dlkm /odm 2>/dev/null',
            "}",
            "",
            "manage_logical_partition() {",
            '    op="$1"; part="$2"; size="$3"; slot="$4"',
            '    case "$op" in',
            '        clear) lptools unmap "$part$slot" && lptools remove "$part$slot" ;;',
            '        create) lptools create "$part$slot" "$size" || checkExit ;;',
            '        create_optional) lptools create "$part$slot" "$size" || true ;;',
            '        map) lptools map "$part$slot" || checkExit ;;',
            '    esac',
            "}",
            "",
            'unzip -o "$ZIPFILE" META-INF/zstd -d /tmp >/dev/null 2>&1',
            "chmod 0755 /tmp/META-INF/zstd 2>/dev/null",
            'unzip -o "$ZIPFILE" META-INF/bin/* -d /tmp >/dev/null 2>&1',
            "chmod 0755 /tmp/META-INF/bin/* 2>/dev/null",
            "",
            'ui_print "============================================"',
            'ui_print "Flashable ROM By Mehraan"',
            f'ui_print "Device     : {device}"',
            f'ui_print "Codename   : {codename}"',
            f'ui_print "Version    : {firmware}"',
            f'ui_print "Maintainer : {maintainer}"',
            'ui_print "============================================"',
            'ui_print " "',
            "checkDevice",
            "unmountPartitions",
            "",
            'SLOT=$(getprop ro.boot.slot_suffix)',
            'ui_print "Checking boot slot... ${SLOT}"',
            'OTHER_SLOT="_a"',
            '[ "$SLOT" = "_a" ] && OTHER_SLOT="_b"',
            "lptools clear-cow",
            "checkExit",
            ""
        ]

        if firmware_imgs:
            sb.append('ui_print "Patching firmware to both slot..."')
            for fw in firmware_imgs:
                sb.append(f'flash_firmware_both_slots "{fw}.img" "{fw}"')
            sb.append("")

        if system_imgs:
            sb.append('ui_print "Patching system..."')
            for sys_part in system_imgs:
                sb.append(f'flash_partition "{sys_part}.img" "/dev/block/by-name/{sys_part}$SLOT" "- Flashing partition {sys_part}"')
            sb.append("")

        # AVB 2.0 (vbmeta) snippet
        if vbmeta_option == "disable":
            sb.extend([
                'ui_print "- Configuring AVB 2.0 (Vbmeta)..."',
                'AVB_BIN="/tmp/META-INF/bin/avbctl"',
                '[ ! -f "$AVB_BIN" ] && AVB_BIN="avbctl"',
                'if [ -f "$AVB_BIN" ] || which avbctl >/dev/null 2>&1; then',
                '    $AVB_BIN --force disable-verity >/dev/null 2>&1 || true',
                '    $AVB_BIN --force disable-verification >/dev/null 2>&1 || true',
                '    ui_print "  • AVB Status : Disabled [dm-verity & verification OFF]"',
                'fi',
                ""
            ])
        elif vbmeta_option == "enable":
            sb.extend([
                'ui_print "- Configuring AVB 2.0 (Vbmeta)..."',
                'AVB_BIN="/tmp/META-INF/bin/avbctl"',
                '[ ! -f "$AVB_BIN" ] && AVB_BIN="avbctl"',
                'if [ -f "$AVB_BIN" ] || which avbctl >/dev/null 2>&1; then',
                '    $AVB_BIN --force enable-verity >/dev/null 2>&1 || true',
                '    $AVB_BIN --force enable-verification >/dev/null 2>&1 || true',
                '    ui_print "  • AVB Status : Enabled [Strict Verification ON]"',
                'fi',
                ""
            ])

        all_super = [p[0] for p in super_specs] + [p[0] for p in tr_specs]
        if all_super:
            sb.append('ui_print "Patching super partitions..."')
            for part in all_super:
                sb.append(f'manage_logical_partition "clear" "{part}" "" "$SLOT"')
                sb.append(f'manage_logical_partition "clear" "{part}" "" "$OTHER_SLOT"')

            for part, size in super_specs:
                sb.append(f'manage_logical_partition "create" "{part}" "{size}" "$SLOT"')
                sb.append(f'manage_logical_partition "create_optional" "{part}" "0" "$OTHER_SLOT"')

            for part, size in tr_specs:
                sb.append(f'manage_logical_partition "create" "{part}" "{size}" "$SLOT"')
                sb.append(f'manage_logical_partition "create_optional" "{part}" "0" "$OTHER_SLOT"')

            for part in all_super:
                sb.append(f'manage_logical_partition "map" "{part}" "" "$SLOT"')

            sb.append("")
            for part, _ in super_specs:
                sb.append(f'flash_partition_zstd "{part}.img.zst" "/dev/block/mapper/{part}$SLOT"')

            for part, _ in tr_specs:
                sb.append(f'flash_partition_zstd "{part}.img.zst" "/dev/block/mapper/{part}$SLOT"')

        sb.extend([
            "",
            'ui_print "============================================"',
            'ui_print "ROM Installed Successfully!"',
            'ui_print "Flashing Script By Mehraan"',
            'ui_print "============================================"',
            "exit 0"
        ])
        return "\n".join(sb)

    @classmethod
    def package_zip_ultra_fast(cls, work_dir: str, output_zip: str):
        """
        Creates the final ZIP package at NVMe write line rate using native 7z/zip STORE mode.
        """
        print(f"[*] [ZIP Packaging] Building final package: {output_zip}")
        abs_output = os.path.abspath(output_zip)
        if os.path.exists(abs_output):
            os.remove(abs_output)

        if shutil.which("7z"):
            # -mx0 = Store (0 compression, instant write), -mmt=on = multi-threaded parallel blocks
            cmd = ["7z", "a", "-tzip", "-mx0", "-mmt=on", abs_output, "."]
            res = subprocess.run(cmd, cwd=work_dir, stdout=subprocess.DEVNULL)
            if res.returncode != 0:
                raise RuntimeError(f"7z packaging failed with exit code {res.returncode}")
        elif shutil.which("zip"):
            cmd = ["zip", "-0", "-q", "-r", abs_output, "."]
            subprocess.run(cmd, cwd=work_dir, check=True)
        else:
            import zipfile
            with zipfile.ZipFile(abs_output, "w", zipfile.ZIP_STORED) as z:
                for root, _, files in os.walk(work_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        rp = os.path.relpath(fp, work_dir).replace("\\", "/")
                        z.write(fp, rp)

    @classmethod
    def build(
        cls,
        partitions: Dict[str, Dict[str, Any]],
        output_zip: str,
        device: str,
        firmware: str,
        codename: str,
        maintainer: str = "Mehraan",
        vbmeta_option: str = "skip",
        zstd_level: int = 1
    ) -> str:
        """Executes full pipeline: zero-copy staging, parallel zstd, updater script, and fast ZIP."""
        work_dir = os.path.abspath("zip_workspace")
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        meta_dir = os.path.join(work_dir, "META-INF", "com", "google", "android")
        os.makedirs(meta_dir, exist_ok=True)

        super_compress_tasks = []
        super_specs = []
        tr_specs = []
        system_imgs = []
        firmware_imgs = []

        for name, info in partitions.items():
            src_path = info["path"]
            is_zst = info["is_zstd"]

            if name in SUPER_PARTITIONS or name in SUPER_TR_PARTITIONS:
                target_file = os.path.join(work_dir, f"{name}.img.zst")
                if is_zst:
                    # ZERO-COPY PASS-THROUGH (0.00 seconds)
                    print(f"[*] [Zero-Copy] Pre-compressed: {name}.img.zst -> Pass-Through staged.")
                    fast_stage_file(src_path, target_file)
                    raw_size = PartitionExtractor.get_zstd_uncompressed_size(src_path)
                    if name in SUPER_PARTITIONS:
                        super_specs.append((name, raw_size))
                    else:
                        tr_specs.append((name, raw_size))
                else:
                    raw_size = os.path.getsize(src_path)
                    super_compress_tasks.append((name, src_path, target_file, zstd_level, raw_size))
            elif name in SYSTEMS:
                target_file = os.path.join(work_dir, f"{name}.img")
                fast_stage_file(src_path, target_file)
                system_imgs.append(name)
            else:
                target_file = os.path.join(work_dir, f"{name}.img")
                fast_stage_file(src_path, target_file)
                firmware_imgs.append(name)

        # Parallel Multi-Core ZSTD Compression for raw partitions
        if super_compress_tasks:
            workers = min(len(super_compress_tasks), os.cpu_count() or 4)
            print(f"[*] [Parallel Zstd Engine] Launching {workers} workers (Level {zstd_level} --fast=1)...")
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(compress_single_image_worker, t) for t in super_compress_tasks]
                for f in as_completed(futures):
                    name, raw_size = f.result()
                    if name in SUPER_PARTITIONS:
                        super_specs.append((name, raw_size))
                    else:
                        tr_specs.append((name, raw_size))

        # Stage static recovery ARM64 zstd binary and avbctl
        zstd_rec_path = os.path.join(work_dir, "META-INF", "zstd")
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zstd_src = os.path.join(script_dir, "bin", "zstd-arm64")
        if os.path.exists(zstd_src):
            fast_stage_file(zstd_src, zstd_rec_path)
        else:
            with open(zstd_rec_path, "wb") as f:
                f.write(b"")

        bin_dir_target = os.path.join(work_dir, "META-INF", "bin")
        os.makedirs(bin_dir_target, exist_ok=True)
        bin_dir_src = os.path.join(script_dir, "bin", "device")
        if os.path.exists(bin_dir_src):
            for b in os.listdir(bin_dir_src):
                fast_stage_file(os.path.join(bin_dir_src, b), os.path.join(bin_dir_target, b))

        # Write updater scripts
        update_binary_content = cls.generate_update_binary(
            device, firmware, codename, super_specs, system_imgs, firmware_imgs, tr_specs,
            maintainer=maintainer, vbmeta_option=vbmeta_option
        )
        update_binary_path = os.path.join(meta_dir, "update-binary")
        with open(update_binary_path, "w", newline="\n") as f:
            f.write(update_binary_content)
        try:
            os.chmod(update_binary_path, 0o755)
        except OSError:
            pass

        with open(os.path.join(meta_dir, "updater-script"), "w", newline="\n") as f:
            f.write("# Dummy updater-script\n")

        # Ultra-fast native packaging
        cls.package_zip_ultra_fast(work_dir, output_zip)
        shutil.rmtree(work_dir, ignore_errors=True)

        size_mb = os.path.getsize(output_zip) / (1024 * 1024)
        print(f"[+] [SUCCESS] Flashable ZIP package ready: {output_zip} ({size_mb:.2f} MB)")
        return output_zip
