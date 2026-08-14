# 🚀 Flashable-Engine

> **Universal Cloud & Local Flashable ROM Maker Engine**  
> *Flashing Scripts & Architecture By **Mehraan***

Automated Android ROM Flashable Package Builder with **GitHub Actions Server CI/CD integration**, high-speed multi-threaded cloud downloading (Google Drive, SourceForge, MediaFire, Direct links), dynamic partition recreation, and **built-in AVB 2.0 / Vbmeta controls** (no extra zips needed).

---

## 🌟 Key Features

- ⚡ **GitHub Actions Server Automation**: Build 5GB+ custom ROM flashable packages in minutes on GitHub cloud runners without consuming your local bandwidth or CPU.
- 📥 **Universal Multi-Threaded Downloader**: Accelerated downloads using `aria2c` (16 parallel connections) supporting:
  - **Google Drive** (Auto large-file token confirmation)
  - **SourceForge** (Direct mirror CDN scraper)
  - **MediaFire** (Direct link resolution)
  - **GitHub Releases / Direct HTTP/HTTPS URLs**
- 🛡️ **Integrated AVB 2.0 / Vbmeta Options (Built-in Script)**:
  - `disable`: Automatically disables dm-verity and verification flags directly inside the recovery `update-binary` using embedded `avbctl`. **No separate vbmeta ZIPs required.**
  - `enable`: Re-enables strict Android Verified Boot.
  - `skip`: Preserves stock/original vbmeta flags untouched.
- 🎨 **Aesthetic Monospace Recovery Console UI**:
  - Centered `Flashing Script By Mehraan` box-lining banner designed for flawless rendering in TWRP, OrangeFox, PBRP, and Lineage Recovery.
- 🗜️ **High-Throughput Compression**:
  - Multi-threaded `zstd -T0` parallel compression for dynamic partitions (`system`, `vendor`, `product`, etc.).
  - On-the-fly streaming decompression straight to `/dev/block/mapper/*` via embedded `zstd-arm64`.
- 💻 **Dual-Mode Hybrid Package**:
  - Ready-to-flash **Recovery ZIP** + PC **Fastboot Flasher** (`windows_flash.bat` & `linux_flash.sh` with bundled fastboot binaries).

---

## 📂 Repository Structure

```text
Flashable-Engine/
├── .github/
│   └── workflows/
│       └── build_flashable.yml    # Complete GitHub Actions Cloud CI/CD workflow
├── bin/
│   ├── device/                    # ARM64 device binaries embedded into flashable zips
│   │   ├── avbctl                 # Native Android Verified Boot controller
│   │   ├── zstd-arm64             # ARM64 high-speed decompression binary
│   │   ├── lptools                # Dynamic partition manager
│   │   ├── lpmake                 # Super image metadata generator
│   │   └── lpdump                 # Logical partition table dumper
│   ├── host/                      # Statically-compiled x86_64 Linux tools
│   │   ├── payload-extract        # Rust-based high-speed payload.bin dumper
│   │   ├── ota_extractor          # Official AOSP payload unpacker
│   │   ├── lpunpack               # Super.img unpacker
│   │   ├── extract.erofs / mkfs   # Modern EROFS rootfs utilities
│   │   ├── simg2img               # Sparse image converter
│   │   └── zstd                   # Multi-threaded host compressor
│   └── fastboot/                  # Standalone PC Fastboot flasher binaries (Win/Linux)
├── core/
│   ├── downloader.py              # Universal 16-thread cloud downloader
│   ├── extractor.py               # Smart ROM, Payload, and Super extractor
│   ├── avb_manager.py             # AVB 2.0 & Vbmeta script logic & image patcher
│   └── builder.py                 # Master Flashable ZIP & Fastboot builder
├── config/
│   └── build_config.example.json  # Device & build profile configuration
├── main.py                        # Unified CLI entry point
├── requirements.txt               # Python dependencies
└── README.md
```

---

## ☁️ How to Build via GitHub Actions (Cloud Server)

1. **Push this repository to GitHub** (Public or Private):
   ```bash
   git init
   git add .
   git commit -m "Initialize Flashable-Engine by Mehraan"
   git remote add origin https://github.com/YOUR_USERNAME/Flashable-Engine.git
   git push -u origin main
   ```

2. **Open the "Actions" tab** in your GitHub repository.
3. Select **"Build Flashable ROM Package"** from the left sidebar.
4. Click **"Run workflow"** and provide the parameters:

| Input Field | Description | Example |
| :--- | :--- | :--- |
| **`rom_url`** | Download link to your ROM archive / payload.bin | `https://drive.google.com/file/d/...` |
| **`device_name`** | Full name of the target device | `POCO F3` |
| **`device_codename`** | Device hardware codename | `alioth` |
| **`rom_version`** | Firmware or ROM version string | `v1.0.0-Stable` |
| **`maintainer`** | Author / Maintainer name | `Mehraan` |
| **`vbmeta_option`** | AVB action (`disable`, `enable`, or `skip`) | `disable` |
| **`compression_format`** | Compression algorithm (`zstd`, `raw`, `erofs`) | `zstd` |
| **`include_fastboot`** | Include PC Fastboot flasher scripts | `true` |
| **`upload_target`** | Where to upload the output ZIP | `github_release` / `transfer_sh` / `all` |

5. Click **"Run workflow"**. The GitHub runner will download, unpack, process AVB flags, compress, and publish your flashable ZIP artifact to GitHub Releases!

---

## 💻 How to Run Locally (CLI)

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Building from a Download URL
```bash
python main.py \
  --url "https://sourceforge.net/projects/sample/files/rom.zip/download" \
  --device "POCO F3" \
  --codename "alioth" \
  --version "v1.0.0-Stable" \
  --maintainer "Mehraan" \
  --vbmeta "disable" \
  --compression "zstd" \
  --output "./output"
```

### 3. Building from a Local Extracted ROM Folder
```bash
python main.py \
  --rom-dir "./my_extracted_rom" \
  --device "Xiaomi 11T" \
  --codename "agate" \
  --version "HyperOS-1.0.4" \
  --maintainer "Mehraan" \
  --vbmeta "skip"
```

---

## 📱 Recovery Console Preview

When the generated package is flashed in TWRP / OrangeFox, it renders:

```text
 ╔══════════════════════════════════════════════╗ 
 ║                                              ║ 
 ║          Flashing Script By Mehraan          ║ 
 ║                                              ║ 
 ╠══════════════════════════════════════════════╣ 
 ║                                              ║ 
 ║   • Device    : POCO F3                      ║ 
 ║   • Codename  : alioth                       ║ 
 ║   • Version   : v1.0.0-Stable                ║ 
 ║                                              ║ 
 ╚══════════════════════════════════════════════╝ 

- Target Slot : _a
  • Flashing boot (Slot A & B)...
  • Flashing dtbo (Slot A & B)...
  • Flashing vendor_boot (Slot A & B)...

 ╔══════════════════════════════════════════════╗ 
 ║        Configuring Android Verified Boot     ║ 
 ╚══════════════════════════════════════════════╝ 
- Checking current AVB vbmeta status...
  • Verity       : disabled
  • Verification : disabled

- Provisioning logical dynamic partitions...
- Streaming logical partitions...
  • Flashing logical partition: system
  • Flashing logical partition: vendor
  • Flashing logical partition: product

 ╔══════════════════════════════════════════════╗ 
 ║          ROM Successfully Flashed!           ║ 
 ╚══════════════════════════════════════════════╝ 
```

---

## ⚖️ License
Created with ❤️ by **Mehraan**. Free for custom ROM developers and maintainers.
