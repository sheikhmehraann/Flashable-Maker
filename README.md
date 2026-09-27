# SpeedFlasher (Flashable Maker)

Universal Android Flashable Package Maker for Windows, Linux, and Android Termux.

Converts partition image dumps (`.img` or `.img.zst`) into flashable recovery ZIPs (compatible with TWRP, OrangeFox, PBRP, and Lineage Recovery) and multi-platform Fastboot flasher scripts (`flash_windows.bat`, `flash_linux.sh`, `flash_termux.sh`).

## Features

- Platform Support: Windows (x86_64), Linux (x86_64), and Android Termux (ARM64).
- Recovery Installer: Self-contained POSIX `update-binary` supporting dynamic partitions (via `lptools`), slot detection (A/B and A-only), and in-memory streaming Zstandard decompression directly to block devices.
- Fastboot Installers: Generates ready-to-run Fastboot flasher scripts for Windows, Linux, and Termux with bundled tools and on-the-fly partition decompression.
- AVB 2.0 (Vbmeta) Control: Directly inspects and patches AVB0 header flags (`disable`, `enable`, or `skip`) across `vbmeta`, `vbmeta_system`, and `vbmeta_vendor`.
- Partition Classification: Automatically identifies dynamic partitions (`system`, `vendor`, `product`, `system_ext`, etc.), direct bootchain images (`boot`, `dtbo`, `init_boot`, `vendor_boot`, `vbmeta`), and firmware images (`lk`, `logo`, `md1img`, `tee`, etc.).
- Multi-Threaded Compression: Parallel Zstandard compression (levels 0-22) with configurable ZIP compression (levels 0-9) and standard Zip64 support.
- Dependency Auto-Resolution: Automatically verifies and installs missing platform dependencies on startup.
- Clean Output Summary: Displays a full breakdown of packaged partitions, installers, output path, and file size, with terminal window persistence.

## Project Structure

```text
Flashable-Maker/
├── bin/
│   ├── device/                  # ARM64 recovery binaries (lptools, avbctl, zstd-arm64, etc.)
│   ├── linux/                   # Linux host tools (fastboot, zstd, lpunpack, etc.)
│   └── windows/                 # Windows host tools (fastboot.exe, zstd.exe, DLLs)
├── core/
│   ├── avb.py                   # AVB 2.0 vbmeta header parser and flag patcher
│   ├── builder.py               # Package staging, multi-threaded compression, and ZIP packaging
│   ├── partitions.py            # Partition image scanning and filesystem detection
│   ├── scripts.py               # Shared utility scripts
│   ├── linux/
│   │   ├── installer.py         # Linux Fastboot shell script generator
│   │   └── platform.py          # Linux dependency checker and tool resolver
│   ├── recovery/
│   │   └── updater.py           # Recovery POSIX update-binary shell generator
│   ├── termux/
│   │   ├── installer.py         # Termux Fastboot shell script generator
│   │   └── platform.py          # Termux environment setup and package manager installer
│   └── windows/
│       ├── installer.py         # Windows Fastboot batch script generator
│       └── platform.py          # Windows dependency checker and tool resolver
├── output/                      # Default build target directory
├── tests/
│   └── test_speedflasher.py     # Multi-OS unit and integration test suite
├── main.py                      # Interactive CLI and headless entrypoint
├── requirements.txt             # Python requirements (zstandard)
├── start.bat                    # Windows launcher
├── start.sh                     # Linux launcher
└── start_termux.sh              # Termux launcher
```

## Quick Start

### Windows
Double-click `start.bat` or run:
```cmd
python main.py
```

### Linux
Make the launcher executable and run:
```bash
chmod +x start.sh
./start.sh
```

### Android Termux
```bash
chmod +x start_termux.sh
./start_termux.sh
```

## Interactive Prompts

When running without arguments, the tool interactively prompts for configuration:

```text
========================================================================
                              SpeedFlasher
========================================================================

Enter IMGS Path : C:\path\to\dumped_images
Devicename : Infinix GT 20 Pro
Codename : X6871
Version : 15.1.2.180
AVB 2.0 (vbmeta) : disable
Maintainer : Mehraan
Ztsd Compression (0-22) : 1
Zip Compression (0-9) : 1
```

Once the build finishes, the tool prints a structured summary and waits for Enter before closing:

```text
========================================================================
                      SpeedFlasher Build Summary
========================================================================
Device Name        : Infinix GT 20 Pro
Codename           : X6871
ROM Version        : 15.1.2.180
Maintainer         : Mehraan
AVB 2.0 (vbmeta)   : DISABLE
ZSTD Compression   : Level 1
ZIP Compression    : Level 1
------------------------------------------------------------------------
Partitions Packaged: Total 12
  - Dynamic (Super): 4 (system, vendor, product, system_ext)
  - Direct (System): 5 (boot, dtbo, init_boot, vendor_boot, vbmeta)
  - Firmware/Boot  : 3 (lk, logo, md1img)
------------------------------------------------------------------------
Installers Generated:
  - Recovery ZIP    : META-INF/com/google/android/update-binary
  - Windows Fastboot: flash_windows.bat (with bundled tools)
  - Linux Fastboot  : flash_linux.sh
  - Termux Fastboot : flash_termux.sh
------------------------------------------------------------------------
Output File        : output/15.1.2.180-X6871-Flashable.zip
Package Size       : 1845.20 MB
Status             : SUCCESS
========================================================================

Press Enter to exit...
```

## Command Line Usage

For automated environments, pass arguments directly:

```bash
python main.py \
  --imgs-path /path/to/images \
  --device "Infinix GT 20 Pro" \
  --codename "X6871" \
  --version "15.1.2.180" \
  --maintainer "Mehraan" \
  --vbmeta disable \
  --zstd-level 1 \
  --zip-level 1
```

## Running Tests

Execute the comprehensive test suite across all OS modules:

```bash
python -m unittest discover tests
```

## License

MIT License. See [LICENSE](file:///C:/Users/Admin/Videos/Github/Flashable-Maker/LICENSE) for details.
