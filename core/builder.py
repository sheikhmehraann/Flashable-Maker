#!/usr/bin/env python3
"""
Flashable-Engine: Master ROM Packaging Engine
Builds high-performance Recovery Flashable ZIPs & Hybrid Fastboot Packages.
Features centered 'Flashing Script By Mehraan' box linings, integrated AVB 2.0, and dynamic partition handling.
"""

import os
import sys
import shutil
import zipfile
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.avb_manager import AvbManager

SUPER_PARTITIONS = [
    "system", "vendor", "product", "system_dlkm", "system_ext",
    "vendor_dlkm", "odm_dlkm", "odm", "cust", "my_heytap", "my_stock",
    "my_carrier", "my_region", "my_company", "my_preload", "my_engineering",
    "tr_carrier", "tr_company", "tr_mi", "tr_overlayfs", "tr_preload",
    "tr_product", "tr_region", "tr_theme", "tr_manifest", "tr_misc"
]

BOOT_PARTITIONS = [
    "boot", "init_boot", "vendor_boot", "dtbo", "vbmeta", "vbmeta_system", "vbmeta_vendor"
]


class FlashableBuilder:
    """Builds ready-to-flash recovery ZIPs and PC fastboot packages."""

    def __init__(
        self,
        device_name: str = "POCO F3",
        codename: str = "alioth",
        version: str = "v1.0.0-Stable",
        maintainer: str = "Mehraan",
        vbmeta_option: str = "disable",
        compression: str = "zstd",
        include_fastboot: bool = True,
        bin_dir: Optional[Path] = None,
        output_dir: str = "./output"
    ):
        self.device_name = device_name
        self.codename = codename
        self.version = version
        self.maintainer = maintainer
        self.vbmeta_option = vbmeta_option
        self.compression = compression
        self.include_fastboot = include_fastboot

        self.root_dir = Path(__file__).resolve().parent.parent
        self.bin_dir = bin_dir or (self.root_dir / "bin")
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.avb_manager = AvbManager(mode=self.vbmeta_option)

    def build_flashable_zip(self, staged_dir: Path) -> Path:
        """
        Takes staged partition files, applies AVB flags, compresses super blocks,
        generates update-binary scripts, and packages into a ZIP.
        """
        print(f"\n[BUILDER] ========================================================")
        print(f"[BUILDER]   Building Flashable Package for {self.device_name} ({self.codename})")
        print(f"[BUILDER]   Maintainer   : {self.maintainer}")
        print(f"[BUILDER]   Version      : {self.version}")
        print(f"[BUILDER]   VBmeta Mode  : {self.vbmeta_option.upper()}")
        print(f"[BUILDER]   Compression  : {self.compression.upper()}")
        print(f"[BUILDER] ========================================================\n")

        staged_dir = Path(staged_dir).resolve()
        tmp_build_dir = staged_dir / "build_staging"
        if tmp_build_dir.exists():
            shutil.rmtree(tmp_build_dir)
        tmp_build_dir.mkdir(parents=True, exist_ok=True)

        # 1. AVB 2.0 Patching on local images (if present)
        for vb_img in ["vbmeta.img", "vbmeta_system.img", "vbmeta_vendor.img"]:
            vb_path = staged_dir / vb_img
            if vb_path.exists():
                self.avb_manager.patch_vbmeta_image(vb_path)

        # 2. Discover available partitions
        found_super = []
        found_super_specs = []
        for part in SUPER_PARTITIONS:
            img = staged_dir / f"{part}.img"
            if img.exists():
                found_super.append(part)
                found_super_specs.append(f"{part}:{img.stat().st_size}")

        found_boot = [part for part in BOOT_PARTITIONS if (staged_dir / f"{part}.img").exists()]
        
        firmware_dir = staged_dir / "firmware"
        found_firmware = [f.stem for f in firmware_dir.glob("*.img")] if firmware_dir.exists() else []

        print(f"[BUILDER] Super Partitions ({len(found_super)}): {', '.join(found_super)}")
        print(f"[BUILDER] Boot/System Images ({len(found_boot)}): {', '.join(found_boot)}")
        print(f"[BUILDER] Firmware Images ({len(found_firmware)}): {', '.join(found_firmware)}")

        # 3. Compress / Stage Super Partitions
        print("\n[BUILDER] Processing Super Partitions...")
        for part in found_super:
            src_img = staged_dir / f"{part}.img"
            if self.compression == "zstd":
                dest_zst = tmp_build_dir / f"{part}.img.zst"
                print(f"  • Compressing {part}.img -> {dest_zst.name} (zstd multithreaded)...")
                self._compress_zstd(src_img, dest_zst)
            else:
                shutil.copy2(src_img, tmp_build_dir / f"{part}.img")

        # 4. Copy Boot & System Images
        print("\n[BUILDER] Staging Boot & Recovery Images...")
        for part in found_boot:
            src_img = staged_dir / f"{part}.img"
            shutil.copy2(src_img, tmp_build_dir / f"{part}.img")

        # 5. Copy Firmware Images
        if found_firmware:
            print("\n[BUILDER] Staging Firmware Images...")
            dest_fw = tmp_build_dir / "firmware"
            dest_fw.mkdir(parents=True, exist_ok=True)
            for fw in found_firmware:
                shutil.copy2(firmware_dir / f"{fw}.img", dest_fw / f"{fw}.img")

        # 6. Copy Device Binaries (zstd-arm64, avbctl, lptools)
        meta_inf = tmp_build_dir / "META-INF" / "com" / "google" / "android"
        meta_inf.mkdir(parents=True, exist_ok=True)
        meta_bin = tmp_build_dir / "META-INF" / "bin"
        meta_bin.mkdir(parents=True, exist_ok=True)

        device_bin_dir = self.bin_dir / "device"
        if (device_bin_dir / "zstd-arm64").exists():
            shutil.copy2(device_bin_dir / "zstd-arm64", tmp_build_dir / "META-INF" / "zstd")
        if (device_bin_dir / "avbctl").exists():
            shutil.copy2(device_bin_dir / "avbctl", meta_bin / "avbctl")
        if (device_bin_dir / "lptools").exists():
            shutil.copy2(device_bin_dir / "lptools", meta_bin / "lptools")

        # 7. Generate Recovery update-binary script
        print("\n[BUILDER] Generating update-binary script...")
        update_binary_content = self._generate_update_binary(
            found_super=found_super,
            found_super_specs=found_super_specs,
            found_boot=found_boot,
            found_firmware=found_firmware
        )
        with open(meta_inf / "update-binary", "w", encoding="utf-8", newline="\n") as f:
            f.write(update_binary_content)

        with open(meta_inf / "updater-script", "w", encoding="utf-8", newline="\n") as f:
            f.write("# FLASHABLE INSTALLER BY MEHRAAN\n# update-binary is self-executing shell script\n")

        # 8. Generate Fastboot Scripts (if enabled)
        if self.include_fastboot:
            print("\n[BUILDER] Generating PC Fastboot Flasher (Windows & Linux)...")
            fb_dir = tmp_build_dir / "fastboot-installer"
            fb_dir.mkdir(parents=True, exist_ok=True)
            
            fb_tools_src = self.bin_dir / "fastboot"
            fb_tools_dst = tmp_build_dir / "META-INF" / "bin" / "fastboot"
            if fb_tools_src.exists():
                shutil.copytree(fb_tools_src, fb_tools_dst, dirs_exist_ok=True)

            with open(fb_dir / "windows_flash.bat", "w", encoding="utf-8", newline="\r\n") as f:
                f.write(self._generate_windows_fastboot_bat(found_boot, found_firmware))
            with open(fb_dir / "linux_flash.sh", "w", encoding="utf-8", newline="\n") as f:
                f.write(self._generate_linux_fastboot_sh(found_boot, found_firmware))

        # 9. Package into final ZIP archive
        clean_ver = self.version.replace(" ", "_").replace("/", "-")
        zip_filename = f"{clean_ver}-{self.codename}-Flashable-By-Mehraan.zip"
        final_zip_path = self.output_dir / zip_filename

        print(f"\n[BUILDER] Packaging final ZIP: {final_zip_path.name}...")
        self._create_zip(tmp_build_dir, final_zip_path)

        # 10. Generate Checksums
        self._generate_checksums(final_zip_path)

        # Cleanup
        shutil.rmtree(tmp_build_dir, ignore_errors=True)

        print(f"\n[BUILDER] SUCCESS! Output ready at: {final_zip_path}")
        return final_zip_path

    def _compress_zstd(self, src: Path, dest: Path):
        """Compresses using host zstd binary or python module."""
        host_zstd = self.bin_dir / "host" / "zstd"
        if host_zstd.exists() and os.access(host_zstd, os.X_OK):
            subprocess.run([str(host_zstd), "-T0", "-15", "-q", str(src), "-o", str(dest)], check=True)
        elif shutil.which("zstd"):
            subprocess.run(["zstd", "-T0", "-15", "-q", str(src), "-o", str(dest)], check=True)
        else:
            shutil.copy2(src, dest.with_suffix(""))

    def _create_zip(self, source_dir: Path, output_zip: Path):
        """Builds the final ZIP package with uncompressed streaming for .zst files."""
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(source_dir)
                    # Don't re-compress .zst or binaries
                    compress_type = zipfile.ZIP_STORED if file.endswith(".zst") else zipfile.ZIP_DEFLATED
                    zf.write(full_path, str(rel_path).replace("\\", "/"), compress_type=compress_type)

    def _generate_checksums(self, file_path: Path):
        """Generates MD5 and SHA256 checksum files."""
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                md5.update(chunk)
                sha256.update(chunk)

        md5_file = file_path.with_suffix(".zip.md5")
        sha256_file = file_path.with_suffix(".zip.sha256")

        with open(md5_file, "w") as f:
            f.write(f"{md5.hexdigest()}  {file_path.name}\n")
        with open(sha256_file, "w") as f:
            f.write(f"{sha256.hexdigest()}  {file_path.name}\n")

        print(f"  • MD5    : {md5.hexdigest()}")
        print(f"  • SHA256 : {sha256.hexdigest()}")

    def _generate_update_binary(
        self,
        found_super: List[str],
        found_super_specs: List[str],
        found_boot: List[str],
        found_firmware: List[str]
    ) -> str:
        """Emits the production-grade shell update-binary for TWRP / recovery."""
        avb_snippet = self.avb_manager.generate_recovery_script_snippet()

        super_clear_lines = "\n".join([f'    manage_logical_partition "clear" "{p}" "" "$SLOT"' for p in found_super])
        super_create_lines = "\n".join([f'    manage_logical_partition "create" "{spec.split(":")[0]}" "{spec.split(":")[1]}" "$SLOT"' for spec in found_super_specs])
        super_flash_lines = "\n".join([f'    flash_partition_zstd "{p}.img.zst" "/dev/block/mapper/{p}$SLOT"' for p in found_super])
        super_map_lines = "\n".join([f'    manage_logical_partition "map" "{p}" "" "$SLOT"' for p in found_super])

        boot_flash_lines = "\n".join([f'    flash_firmware_both_slots "{p}.img" "{p}"' for p in found_boot])
        fw_flash_lines = "\n".join([f'    flash_firmware_both_slots "firmware/{fw}.img" "{fw}"' for fw in found_firmware])

        return f"""#!/sbin/sh
# ===========================================================================
# FLASHABLE INSTALLER ENGINE
# Flashing Script By {self.maintainer}
# ===========================================================================

OUTFD=/proc/self/fd/$2
ZIPFILE="$3"

ui_print() {{
    printf 'ui_print %s\\nui_print\\n' "$1" >>"$OUTFD"
}}

flash_partition() {{
    src="$1"
    dest="$2"
    msg="$3"
    [ -n "$msg" ] && ui_print "$msg"
    unzip -p "$ZIPFILE" "$src" >"$dest" || {{
        ui_print "Error: Failed to flash $src to $dest"
        exit 1
    }}
}}

flash_partition_zstd() {{
    src="$1"
    dest="$2"
    pname=$(echo "$dest" | cut -d '/' -f 5)
    ui_print "  • Flashing logical partition: $pname"
    unzip -p "$ZIPFILE" "$src" | /tmp/META-INF/zstd -c -d >"$dest" || {{
        ui_print "Error: Failed to stream-flash $src"
        exit 1
    }}
}}

flash_firmware_both_slots() {{
    img="$1"
    base="$2"
    if [ -e "/dev/block/by-name/${{base}}_a" ]; then
        flash_partition "$img" "/dev/block/by-name/${{base}}_a" "  • Flashing ${{base}} (Slot A & B)..."
        flash_partition "$img" "/dev/block/by-name/${{base}}_b" ""
    elif [ -e "/dev/block/by-name/${{base}}" ]; then
        flash_partition "$img" "/dev/block/by-name/${{base}}" "  • Flashing ${{base}}..."
    fi
}}

checkDevice() {{
    myDev=$(getprop ro.product.device)
    [ -z "$myDev" ] && myDev=$(getprop ro.build.product)
    [ -z "$myDev" ] && myDev=$(getprop ro.product.name)
    targetDev="{self.codename}"
    if [ -n "$targetDev" ] && [ -z "$(echo "$myDev" | grep -i "$targetDev")" ]; then
        ui_print "[WARNING] Device code verification mismatch: Found '$myDev', expected '$targetDev'"
        ui_print "Continuing install under user confirmation..."
    fi
}}

manage_logical_partition() {{
    op="$1"
    part="$2"
    size="$3"
    slot="$4"
    LPT="/tmp/META-INF/bin/lptools"
    [ ! -f "$LPT" ] && LPT="lptools"
    case "$op" in
        clear)
            $LPT unmap "${{part}}${{slot}}" >/dev/null 2>&1 || true
            $LPT remove "${{part}}${{slot}}" >/dev/null 2>&1 || true
            ;;
        create)
            $LPT create "${{part}}${{slot}}" "$size" >/dev/null 2>&1 || true
            ;;
        map)
            $LPT map "${{part}}${{slot}}" >/dev/null 2>&1 || true
            ;;
    esac
}}

# Extract bundled tools
unzip -o "$ZIPFILE" "META-INF/zstd" -d /tmp >/dev/null 2>&1
chmod 0755 /tmp/META-INF/zstd 2>/dev/null
unzip -o "$ZIPFILE" "META-INF/bin/*" -d /tmp >/dev/null 2>&1
chmod 0755 /tmp/META-INF/bin/* 2>/dev/null

        # UI Banner
        ui_print " "
        ui_print " ╔══════════════════════════════════════════════╗ "
        ui_print " ║                                              ║ "
        ui_print " ║          Flashing Script By Mehraan          ║ "
        ui_print " ║                                              ║ "
        ui_print " ╠══════════════════════════════════════════════╣ "
        ui_print " ║                                              ║ "
        ui_print " ║   • Device     : {self.device_name} "
        ui_print " ║   • Codename   : {self.codename} "
        ui_print " ║   • Version    : {self.version} "
        ui_print " ║   • Maintainer : {self.maintainer} "
        ui_print " ║                                              ║ "
        ui_print " ╚══════════════════════════════════════════════╝ "
        ui_print " "

        checkDevice

        # Unmount active partitions
        umount /system /system_root /vendor /product /system_ext /odm /data 2>/dev/null || true

        SLOT=$(getprop ro.boot.slot_suffix)
        [ -z "$SLOT" ] && SLOT="_a"
        ui_print "[*] Target Boot Slot : $SLOT"

        # Clear Virtual A/B Cow space
        /tmp/META-INF/bin/lptools clear-cow >/dev/null 2>&1 || true

        # Firmware Flashing
        if [ "{len(found_firmware)}" -gt "0" ]; then
            ui_print " "
            ui_print "- Flashing firmware partitions..."
{fw_flash_lines}
        fi

        # Boot & Kernel Images
        if [ "{len(found_boot)}" -gt "0" ]; then
            ui_print " "
            ui_print "- Flashing boot & kernel images..."
{boot_flash_lines}
        fi

        # AVB / VBMETA Handling (Built-in Script Routine)
        ui_print " "
{avb_snippet}

        # Dynamic Super Partitions
        if [ "{len(found_super)}" -gt "0" ]; then
            ui_print " "
            ui_print "- Provisioning dynamic partitions (super)..."
{super_clear_lines}
{super_create_lines}
{super_map_lines}
            ui_print "- Streaming logical partitions..."
{super_flash_lines}
        fi

        ui_print " "
        ui_print " ╔══════════════════════════════════════════════╗ "
        ui_print " ║          ROM Successfully Flashed!           ║ "
        ui_print " ║          Flashing Script By Mehraan          ║ "
        ui_print " ╚══════════════════════════════════════════════╝ "
        ui_print " "
        exit 0
        """

    def _generate_windows_fastboot_bat(self, found_boot: List[str], found_firmware: List[str]) -> str:
        """Generates Windows PC Fastboot Batch Flasher."""
        boot_lines = "\n".join([f"%fastboot% flash {p}_ab images\\{p}.img" for p in found_boot if p != "vbmeta"])
        vb_line = "%fastboot% flash vbmeta_ab images\\vbmeta.img --disable-verity --disable-verification" if self.vbmeta_option == "disable" else "%fastboot% flash vbmeta_ab images\\vbmeta.img"

        return f"""@echo off&setlocal enabledelayedexpansion
cd %~dp0
cd ..
title Flashing Script By Mehraan - Fastboot Flasher
set fastboot=META-INF\\bin\\fastboot\\fastboot.exe
if %PROCESSOR_ARCHITECTURE%==x86 (set fastboot_f=META-INF\\bin\\fastboot\\fastboot32.exe) else set fastboot_f=META-INF\\bin\\fastboot\\fastboot64.exe

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                                                      ║
echo  ║              Flashing Script By Mehraan              ║
echo  ║                   FASTBOOT WINDOWS                   ║
echo  ║                                                      ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║                                                      ║
echo  ║   • Device     : {self.device_name}
echo  ║   • Codename   : {self.codename}
echo  ║   • Version    : {self.version}
echo  ║   • Maintainer : {self.maintainer}
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
set /p CHOICE="Format Data? (y/n): "
echo.

echo Flashing images...
{boot_lines}
{vb_line}

echo.
echo ==============================================
echo           ROM INSTALLED SUCCESSFULLY
echo           Flashing Script By Mehraan
if /I "%CHOICE%" == "y" (
    echo Formatting Data...
    %fastboot% erase userdata >NUL 2>NUL
    %fastboot% erase metadata >NUL 2>NUL
    echo Rebooting System...
    %fastboot% reboot
)
pause
"""

    def _generate_linux_fastboot_sh(self, found_boot: List[str], found_firmware: List[str]) -> str:
        """Generates Linux PC Fastboot Shell Flasher."""
        boot_lines = "\n".join([f"$fastboot flash {p}_ab images/{p}.img" for p in found_boot if p != "vbmeta"])
        vb_line = "$fastboot flash vbmeta_ab images/vbmeta.img --disable-verity --disable-verification" if self.vbmeta_option == "disable" else "$fastboot flash vbmeta_ab images/vbmeta.img"

        return f"""#!/bin/bash
cd $(dirname $0)
cd ..
fastbootbins=META-INF/bin/fastboot
fastboot=$fastbootbins/fastboot
chmod 755 $fastbootbins/*

echo ""
echo " ╔══════════════════════════════════════════════════════╗"
echo " ║                                                      ║"
echo " ║              Flashing Script By Mehraan              ║"
echo " ║                    FASTBOOT LINUX                    ║"
echo " ║                                                      ║"
echo " ╠══════════════════════════════════════════════════════╣"
echo " ║                                                      ║"
echo " ║   • Device     : {self.device_name}"
echo " ║   • Codename   : {self.codename}"
echo " ║   • Version    : {self.version}"
echo " ║   • Maintainer : {self.maintainer}"
echo " ║                                                      ║"
echo " ╚══════════════════════════════════════════════════════╝"
echo ""
read -p "Format Data? (y/n): " CHOICE

echo "Flashing images..."
{boot_lines}
{vb_line}

echo ""
echo "=============================================="
echo "          ROM INSTALLED SUCCESSFULLY          "
echo "          Flashing Script By Mehraan          "
if [[ $CHOICE == y ]]; then
    echo "Formatting Data..."
    $fastboot erase userdata > /dev/null 2>&1
    $fastboot erase metadata > /dev/null 2>&1
    echo "Rebooting..."
    $fastboot reboot
fi
"""

echo.
echo ==============================================
echo           ROM INSTALLED SUCCESSFULLY
if /I "%CHOICE%" == "y" (
    echo Formatting Data...
    %fastboot% erase userdata >NUL 2>NUL
    %fastboot% erase metadata >NUL 2>NUL
    echo Rebooting System...
    %fastboot% reboot
)
pause
"""

    def _generate_linux_fastboot_sh(self, found_boot: List[str], found_firmware: List[str]) -> str:
        """Generates Linux PC Fastboot Shell Flasher."""
        boot_lines = "\n".join([f"$fastboot flash {p}_ab images/{p}.img" for p in found_boot if p != "vbmeta"])
        vb_line = "$fastboot flash vbmeta_ab images/vbmeta.img --disable-verity --disable-verification" if self.vbmeta_option == "disable" else "$fastboot flash vbmeta_ab images/vbmeta.img"

        return f"""#!/bin/bash
cd $(dirname $0)
cd ..
fastbootbins=META-INF/bin/fastboot
fastboot=$fastbootbins/fastboot
chmod 755 $fastbootbins/*

echo ""
echo " ╔══════════════════════════════════════════════════════╗"
echo " ║                                                      ║"
echo " ║              Flashing Script By {self.maintainer}              ║"
echo " ║                    FASTBOOT LINUX                    ║"
echo " ║                                                      ║"
echo " ╠══════════════════════════════════════════════════════╣"
echo " ║                                                      ║"
echo " ║   • Device    : {self.device_name}                              ║"
echo " ║   • Codename  : {self.codename}                                 ║"
echo " ║   • Version   : {self.version}                        ║"
echo " ║                                                      ║"
echo " ╚══════════════════════════════════════════════════════╝"
echo ""
read -p "Format Data? (y/n): " CHOICE

echo "Flashing images..."
{boot_lines}
{vb_line}

echo ""
echo "=============================================="
echo "          ROM INSTALLED SUCCESSFULLY          "
if [[ $CHOICE == y ]]; then
    echo "Formatting Data..."
    $fastboot erase userdata > /dev/null 2>&1
    $fastboot erase metadata > /dev/null 2>&1
    echo "Rebooting..."
    $fastboot reboot
fi
"""
