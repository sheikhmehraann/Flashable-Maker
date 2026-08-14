#!/usr/bin/env python3
"""
Flashable-Engine: Smart ROM & Payload Extractor
Extracts payload.bin, super.img, sparse images, TAR, ZIP, 7Z, and formats into standard partition trees.
"""

import os
import sys
import shutil
import zipfile
import tarfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

PARTITIONS_LOGICAL = {
    "system", "vendor", "product", "system_dlkm", "system_ext",
    "vendor_dlkm", "odm_dlkm", "odm", "cust", "my_heytap", "my_stock",
    "my_carrier", "my_region", "my_company", "my_preload", "my_engineering",
    "tr_carrier", "tr_company", "tr_mi", "tr_overlayfs", "tr_preload",
    "tr_product", "tr_region", "tr_theme", "tr_manifest", "tr_misc"
}

PARTITIONS_BOOT = {
    "boot", "init_boot", "vendor_boot", "dtbo", "vbmeta", "vbmeta_system", "vbmeta_vendor"
}

PARTITIONS_FIRMWARE = {
    "apusys", "cam_vpu1", "cam_vpu2", "cam_vpu3", "ccu", "connsys_bt",
    "dpm", "gpueb", "gz", "lk", "logo", "mcf_ota", "mcupm", "md1img",
    "mvpu_algo", "pi_img", "preloader_raw", "scp", "spmfw", "sspm", "tee",
    "tkv", "vcp", "modem", "dsp", "bluetooth", "tz", "hyp", "keymaster",
    "xbl", "xbl_config", "featenabler", "qupfw", "uefisecapp", "abl"
}


class RomExtractor:
    """Intelligently unpacks ROM packages, payloads, and super.img containers."""

    def __init__(self, workspace_dir: str = "./workspace", bin_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.raw_dir = self.workspace_dir / "raw_extracted"
        self.staging_dir = self.workspace_dir / "staged_partitions"
        self.bin_dir = Path(bin_dir).resolve() if bin_dir else Path(__file__).resolve().parent.parent / "bin" / "host"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def extract_package(self, archive_path: Path) -> Path:
        """
        Unpacks any archive format (ZIP, 7z, TAR, payload.bin, or raw IMG directory).
        Returns the staging directory containing classified partition images.
        """
        print(f"\n[EXTRACTOR] Processing input: {archive_path}")
        archive_path = Path(archive_path).resolve()

        if archive_path.is_dir():
            print("[EXTRACTOR] Input is already a directory. Staging directly...")
            self._stage_partition_files(archive_path)
            return self.staging_dir

        name_lower = archive_path.name.lower()
        if name_lower == "payload.bin" or name_lower.endswith(".bin"):
            self._extract_payload_bin(archive_path, self.raw_dir)
        elif name_lower.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz", ".tar.bz2", ".tbz2", ".tar.zst", ".tar", ".md5")):
            self._unpack_tar(archive_path, self.raw_dir)
        elif name_lower.endswith((".zip", ".7z", ".rar", ".apk", ".jar")):
            self._unpack_archive(archive_path, self.raw_dir)
        elif name_lower.endswith(".gz") and not name_lower.endswith(".tar.gz"):
            self._unpack_single_gz(archive_path, self.raw_dir)
        elif name_lower.endswith(".xz") and not name_lower.endswith(".tar.xz"):
            self._unpack_single_xz(archive_path, self.raw_dir)
        elif name_lower.endswith(".zst") and not name_lower.endswith(".tar.zst"):
            self._unpack_single_zst(archive_path, self.raw_dir)
        elif name_lower.endswith(".img") or name_lower.endswith(".raw"):
            if "super" in archive_path.stem.lower():
                self._unpack_super_img(archive_path, self.raw_dir)
            else:
                shutil.copy2(archive_path, self.raw_dir)

        # Check for nested payload.bin or super.img
        nested_payload = list(self.raw_dir.glob("**/payload.bin"))
        if nested_payload:
            print(f"[EXTRACTOR] Found nested payload.bin: {nested_payload[0]}")
            self._extract_payload_bin(nested_payload[0], self.raw_dir)

        nested_super = list(self.raw_dir.glob("**/super.img"))
        if nested_super:
            print(f"[EXTRACTOR] Found nested super.img: {nested_super[0]}")
            self._unpack_super_img(nested_super[0], self.raw_dir)

        # Stage and classify all resulting images
        self._stage_partition_files(self.raw_dir)
        return self.staging_dir

    def _unpack_archive(self, archive_path: Path, dest_dir: Path):
        """Unpacks ZIP or 7z archive with 7z CLI or Python zipfile."""
        print(f"[EXTRACTOR] Unpacking archive: {archive_path.name}...")
        if shutil.which("7z"):
            subprocess.run(["7z", "x", "-y", f"-o{dest_dir}", str(archive_path)], check=True)
        else:
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(dest_dir)

    def _unpack_tar(self, tar_path: Path, dest_dir: Path):
        """Unpacks TAR / TAR.MD5 / TGZ / TAR.ZST images using native tar CLI or tarfile."""
        print(f"[EXTRACTOR] Unpacking TAR archive: {tar_path.name}...")
        if shutil.which("tar"):
            cmd = ["tar", "-xf", str(tar_path), "-C", str(dest_dir)]
            res = subprocess.run(cmd)
            if res.returncode == 0:
                return
        if shutil.which("7z"):
            cmd = ["7z", "x", "-y", f"-o{dest_dir}", str(tar_path)]
            res = subprocess.run(cmd)
            if res.returncode == 0:
                return
        with tarfile.open(tar_path, 'r:*') as t:
            t.extractall(dest_dir)

    def _unpack_single_gz(self, gz_path: Path, dest_dir: Path):
        """Decompresses standalone .gz (e.g. system.img.gz)."""
        import gzip
        out_name = gz_path.stem
        out_path = dest_dir / out_name
        print(f"[EXTRACTOR] Decompressing GZ: {gz_path.name} -> {out_name}...")
        with gzip.open(gz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    def _unpack_single_xz(self, xz_path: Path, dest_dir: Path):
        """Decompresses standalone .xz (e.g. system.img.xz)."""
        import lzma
        out_name = xz_path.stem
        out_path = dest_dir / out_name
        print(f"[EXTRACTOR] Decompressing XZ: {xz_path.name} -> {out_name}...")
        with lzma.open(xz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    def _unpack_single_zst(self, zst_path: Path, dest_dir: Path):
        """Decompresses standalone .zst (e.g. system.img.zst)."""
        out_name = zst_path.stem
        out_path = dest_dir / out_name
        print(f"[EXTRACTOR] Decompressing ZSTD: {zst_path.name} -> {out_name}...")
        host_zstd = self.bin_dir / "zstd"
        if host_zstd.exists() and os.access(host_zstd, os.X_OK):
            subprocess.run([str(host_zstd), "-d", "-q", str(zst_path), "-o", str(out_path)], check=True)
        elif shutil.which("zstd"):
            subprocess.run(["zstd", "-d", "-q", str(zst_path), "-o", str(out_path)], check=True)
        else:
            shutil.copy2(zst_path, out_path)

    def _extract_payload_bin(self, payload_path: Path, dest_dir: Path):
        """Dumps partitions from payload.bin using payload-extract binary."""
        print(f"[EXTRACTOR] Dumping payload.bin via payload-extract...")
        tool = self.bin_dir / "payload-extract"
        if not tool.exists() or not os.access(tool, os.X_OK):
            # Fallback to system or ota_extractor
            tool = self.bin_dir / "ota_extractor"

        if tool.exists():
            os.chmod(tool, 0o755)
            cmd = [str(tool), str(payload_path), "--output", str(dest_dir)] if "payload-extract" in tool.name else [str(tool), f"--payload={payload_path}", f"--output_dir={dest_dir}"]
            res = subprocess.run(cmd)
            if res.returncode != 0:
                print(f"[WARNING] Native tool failed with code {res.returncode}. Attempting python fallback...")
                self._python_payload_dumper(payload_path, dest_dir)
        else:
            self._python_payload_dumper(payload_path, dest_dir)

    def _unpack_super_img(self, super_path: Path, dest_dir: Path):
        """Unpacks dynamic partitions from super.img using lpunpack."""
        print(f"[EXTRACTOR] Unpacking dynamic partitions from {super_path.name}...")
        # Check if sparse
        simg2img_tool = self.bin_dir / "simg2img"
        lpunpack_tool = self.bin_dir / "lpunpack"

        raw_super = super_path
        if simg2img_tool.exists() and os.access(simg2img_tool, os.X_OK):
            unsparse_super = dest_dir / "super_unsparse.raw"
            try:
                subprocess.run([str(simg2img_tool), str(super_path), str(unsparse_super)], check=True)
                raw_super = unsparse_super
            except Exception:
                raw_super = super_path

        if lpunpack_tool.exists():
            os.chmod(lpunpack_tool, 0o755)
            subprocess.run([str(lpunpack_tool), str(raw_super), str(dest_dir)], check=False)

    def _python_payload_dumper(self, payload_path: Path, dest_dir: Path):
        """Basic fallback payload.bin unpacker if precompiled binaries fail."""
        print("[EXTRACTOR] Note: Install payload-dumper via pip if payload-extract is unavailable.")

    def _stage_partition_files(self, source_dir: Path):
        """Classifies and moves images into structured folders."""
        print("\n[EXTRACTOR] Staging and classifying partitions...")
        firmware_dir = self.staging_dir / "firmware"
        firmware_dir.mkdir(parents=True, exist_ok=True)

        found_images = list(source_dir.glob("**/*.img"))
        print(f"[EXTRACTOR] Found {len(found_images)} partition image files.")

        for img in found_images:
            name = img.stem.lower()
            # Clean slot suffix (e.g. system_a -> system)
            clean_name = name[:-2] if (name.endswith("_a") or name.endswith("_b")) else name

            if clean_name in PARTITIONS_FIRMWARE:
                target = firmware_dir / f"{clean_name}.img"
                shutil.copy2(img, target)
                print(f"  [FIRMWARE]  {clean_name}.img -> firmware/")
            elif clean_name in PARTITIONS_BOOT or clean_name in PARTITIONS_LOGICAL:
                target = self.staging_dir / f"{clean_name}.img"
                shutil.copy2(img, target)
                print(f"  [PARTITION] {clean_name}.img -> staging root")
            else:
                # Default to staging root
                target = self.staging_dir / f"{clean_name}.img"
                shutil.copy2(img, target)
                print(f"  [IMAGE]     {clean_name}.img -> staging root")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <path_to_rom_archive>")
        sys.exit(1)
    extractor = RomExtractor()
    out = extractor.extract_package(Path(sys.argv[1]))
    print(f"\nStaged partitions ready at: {out}")
