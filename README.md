# ⚡ Flashable-Engine

<div align="center">

```
============================================
         Flashing Script By Mehraan
============================================

Device: Infinix GT 20 Pro
Codename: X6871
Version: 15.1.2.180SP05OP001PF001AZ
Maintainer: Mehraan
============================================
```

**The Universal, High-Performance Android Flashable ROM Package Maker**  
*Next-Gen Native Pipeline • Zero-Copy • Both-Slots Flashing • Smart AVB 2.0 Controls • Instant Cloud Upload*

---

[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=githubactions&logoColor=white)](https://github.com/sheikhmehraann/Flashable-Maker/actions)
[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-brightgreen?logo=python&logoColor=white)](https://python.org)
[![Compression](https://img.shields.io/badge/Compression-Zstandard%20v1.5.6%20(Level%200--22)-orange?logo=zstandard&logoColor=white)](https://facebook.github.io/zstd/)
[![Platform](https://img.shields.io/badge/Platform-Android%20A%2FB%20%7C%20Dynamic%20Partitions-purple?logo=android&logoColor=white)](https://source.android.com)
[![Maintainer](https://img.shields.io/badge/Maintainer-Mehraan-cyan)](https://github.com/sheikhmehraann)

</div>

---

## 🌟 Key Features

- ⚡ **10GB ROMs in Seconds**: Multi-core parallel ZSTD compression pipeline paired with direct stream-decompression to block devices at **>1.8 GB/s** during flashing.
- 🔄 **Both-Slots Flashing Engine**: Automatically discovers and flashes all slotted partitions (`boot`, `vendor_boot`, `init_boot`, `lk`, `logo`, `dtbo`, `vbmeta`, `system`, `vendor`, etc.) to **both slots (`_a` and `_b`)** to prevent hard bricks.
- 🔍 **Dynamic Block Device Discovery**: Universal `find_block_device()` resolver searching across `/dev/block/by-name`, `/dev/block/bootdevice/by-name`, and `/dev/block/platform/*/by-name` ensuring 100% compatibility across **MediaTek, Qualcomm, Samsung Exynos, and Unisoc**.
- 🛡️ **Intelligent AVB 2.0 / Vbmeta Controls**:
  - `enable`: Ensures AVB strict verification is enabled. If already enabled on the device, reports `Already Enabled (Skipped)`.
  - `disable`: Disables dm-verity and verification. If already disabled, reports `Already Disabled (Skipped)`.
  - `skip`: Omits AVB configuration and keeps stock vbmeta intact with zero binary overhead.
- 🗜️ **Universal Recursive Extraction**: Automatically extracts and flattens any archive format (`.tar.zst`, `.zip`, `.7z`, `.rar`, `.tar.gz`, `.tar.xz`, `payload.bin`, `super.img`) containing partition images.
- ☁️ **Turbo GoFile.io Cloud Integration**: Native high-speed upload powered by `gofile-fast-link-transfer` returning instant, publicly accessible download links.
- 🤖 **1-Click GitHub Actions CI/CD**: Build multi-gigabyte custom ROM packages directly in the cloud from any remote download URL without using your local bandwidth or CPU.
- 🎨 **Clean Monospace Recovery Interface**: Minimalist, professional console output designed for TWRP, OrangeFox, PBRP, and Lineage Recovery.

---

## 📱 Live Recovery Flashing UI

When flashing the generated package in custom recovery, users receive this clean, real-time output:

```text
============================================
         Flashing Script By Mehraan
============================================

Device: Infinix GT 20 Pro
Codename: X6871
Version: 15.1.2.180SP05OP001PF001AZ
Maintainer: Mehraan
============================================
 
- Target Device    : Verified X6871
- Active Boot Slot : Slot A
 
Patching firmware to both slots
- Flashing partition lk to both slots
- Flashing partition logo to both slots
 
Patching system
- Flashing partition boot to both slots
 
- Configuring AVB 2.0 (Vbmeta)
  - AVB Status : Already Enabled (Skipped)
 
============================================
           Flashed Successfully!
============================================
```

---

## 📂 Repository Structure

```text
Flashable-Maker/
└── Flashable-Engine/
    ├── .github/
    │   └── workflows/
    │       └── build_flashable.yml    # 1-Click Cloud CI/CD Pipeline
    ├── bin/
    │   ├── device/                    # ARM64 recovery helper binaries
    │   │   ├── avbctl                 # Native Android Verified Boot controller
    │   │   ├── lptools                # Dynamic partition manager
    │   │   ├── lpmake                 # Super image metadata builder
    │   │   └── lpdump                 # Dynamic partition table dumper
    │   └── zstd-arm64                 # Ultra-compact static ARM64 decompressor
    ├── core/
    │   ├── builder.py                 # Flashable ZIP builder & script generator
    │   ├── downloader.py              # Multi-connection parallel downloader
    │   └── extractor.py               # Recursive multi-archive unpacker
    ├── gofile_transfer/               # High-throughput GoFile.io upload engine
    │   ├── resolvers/                 # Link resolvers (GDrive, SourceForge, MediaFire)
    │   ├── downloader.py              # 16-connection aria2c engine
    │   └── uploader.py                # Turbo GoFile upload client
    ├── main.py                        # Unified CLI Entry Point
    ├── requirements.txt               # Python package dependencies
    └── README.md
```

---

## ☁️ 1-Click Cloud Building via GitHub Actions (Free & Zero Setup)

You can build 10GB+ flashable ROM packages entirely in the cloud **without downloading anything to your PC, without using your personal internet data, and without installing any tools or Python!**

### 🚀 Step-by-Step Guide (For Everyone):

1. **🍴 Fork this Repository**:
   - Click the [**Fork**](https://github.com/sheikhmehraann/Flashable-Maker/fork) button at the top-right corner of this repository to create your own personal copy.

2. **⚡ Enable Workflows**:
   - In your newly forked repository, navigate to the **Actions** tab.
   - Click the green button: **"I understand my workflows, go ahead and enable them"**.

3. **▶️ Run the Flashable Builder**:
   - Select **"Build Flashable ROM Package (Flashable-Engine)"** from the left workflow list.
   - Click the **"Run workflow"** button on the right.
   - Fill in your ROM parameters:

| Input Parameter | Description | Default / Example |
| :--- | :--- | :--- |
| **`rom_url`** | Direct download link (Google Drive, SourceForge, MediaFire, Direct Link) | `https://drive.google.com/file/d/...` |
| **`device_name`** | Full Device Marketing Name | `Infinix GT 20 Pro` |
| **`device_codename`** | Hardware Board Codename | `X6871` |
| **`rom_version`** | ROM / Firmware Version String | `15.1.2.180SP05OP001PF001AZ` |
| **`maintainer`** | Maintainer / Author Name | `Mehraan` |
| **`vbmeta_option`** | AVB 2.0 Action (`enable`, `disable`, `skip`) | `enable` |
| **`zstd_level`** | ZSTD Compression Level (`0` to `22`) | `22` (Ultra-Max) |
| **`zip_level`** | ZIP Deflate Level (`0` = Store, `9` = Max) | `9` |

4. **📥 Instant GoFile.io Download Link**:
   - Click **"Run workflow"**.
   - Within 1–2 minutes, GitHub's high-speed cloud runner will download, unpack, build the flashable ZIP, and provide your **instant public GoFile.io download link** directly in the GitHub Job Summary!

---

## 💻 Local Installation & Usage

### 1. Requirements
- Python 3.9+
- `aria2`, `zstd`, `p7zip-full`, `libarchive-tools`, `curl`

#### Linux (Ubuntu/Debian):
```bash
sudo apt update && sudo apt install -y aria2 zstd p7zip-full libarchive-tools curl python3-pip
pip install -r requirements.txt
```

#### Windows:
Make sure Python is installed and added to PATH. Install dependencies:
```powershell
pip install -r requirements.txt
```

---

### 2. Command-Line Examples

#### A. Build from Local Images Directory:
```bash
python main.py \
  --rom-dir "C:\Path\To\My-imgs" \
  --device "Infinix GT 20 Pro" \
  --codename "X6871" \
  --version "15.1.2.180SP05OP001PF001AZ" \
  --maintainer "Mehraan" \
  --vbmeta "enable" \
  --zstd-level 22 \
  --zip-level 9 \
  --output "C:\Path\To\Output"
```

#### B. Build from Local Archive (`.zip`, `.tar.zst`, `payload.bin`):
```bash
python main.py \
  --file "C:\Path\To\rom_dump.tar.zst" \
  --device "Infinix GT 20 Pro" \
  --codename "X6871" \
  --version "15.1.2.180SP05OP001PF001AZ" \
  --maintainer "Mehraan" \
  --vbmeta "enable" \
  --zstd-level 22 \
  --output "./output"
```

#### C. Build from Remote URL + Auto-Upload to GoFile:
```bash
python main.py \
  --url "https://direct-link.com/rom_package.zip" \
  --device "Infinix GT 20 Pro" \
  --codename "X6871" \
  --version "15.1.2.180SP05OP001PF001AZ" \
  --maintainer "Mehraan" \
  --vbmeta "enable" \
  --zstd-level 22 \
  --zip-level 9 \
  --upload "gofile" \
  --output "./output"
```

---

## 🛠️ CLI Flags Reference

| Option | Flag | Description |
| :--- | :--- | :--- |
| **Source URL** | `--url <URL>` | Download from SourceForge, Google Drive, MediaFire, or Direct HTTPS |
| **Local File** | `--file <PATH>` | Input local archive (`.zip`, `.tar.zst`, `.7z`, `payload.bin`, etc.) |
| **Local Directory** | `--rom-dir <PATH>` | Input directory containing extracted `.img` or `.img.zst` files |
| **Device Name** | `--device <STR>` | Target device marketing name (e.g. `Infinix GT 20 Pro`) |
| **Codename** | `--codename <STR>` | Device board codename (e.g. `X6871`) |
| **Version** | `--version <STR>` | Firmware / ROM version string |
| **Maintainer** | `--maintainer <STR>` | Maintainer or author name (Default: `Mehraan`) |
| **AVB Vbmeta** | `--vbmeta <MODE>` | `enable` (default), `disable`, or `skip` |
| **ZSTD Level** | `--zstd-level <0-22>` | `0` = raw pass-through, `1` = ultra-fast, `22` = maximum compression |
| **ZIP Level** | `--zip-level <0-9>` | `0` = store mode (line rate speed), `9` = maximum deflate compression |
| **Cloud Upload** | `--upload <TARGET>` | `none` (default) or `gofile` |
| **Output Path** | `--output <PATH>` | Destination directory or output `.zip` file path |

---

## 📜 Credits & License

- **Flashing Script & Architecture**: **Mehraan** ([@sheikhmehraann](https://github.com/sheikhmehraann))
- **Dynamic Partition Management**: Powered by AOSP `lptools` & `avbctl`
- **Compression Engine**: Facebook Zstandard (`zstd`)
- **Cloud Upload Engine**: `gofile-fast-link-transfer`

Licensed under the **Apache 2.0 License**. Free for personal and community ROM development.
