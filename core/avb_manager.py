#!/usr/bin/env python3
"""
Flashable-Engine: AVB 2.0 & Vbmeta Manager
Integrates AVB 2.0 verification and dm-verity controls directly into flashing scripts and images.
Supports: 'disable', 'enable', and 'skip' modes (no external standalone zip needed).
"""

import os
import struct
from pathlib import Path
from typing import Optional, Tuple

AVB_MAGIC = b"AVB0"
# AVB vbmeta header flags offset: 120 (0x78) or 123 (0x7B) Little Endian flag field
AVB_FLAGS_OFFSET = 120
AVB_FLAG_DISABLE_VERITY = 1
AVB_FLAG_DISABLE_VERIFICATION = 2


class AvbManager:
    """Controls Verified Boot (AVB 2.0) states, vbmeta flags, and script routines."""

    def __init__(self, mode: str = "disable"):
        self.mode = mode.lower().strip()
        if self.mode not in ["disable", "enable", "skip"]:
            raise ValueError(f"Invalid AVB mode: '{mode}'. Must be 'disable', 'enable', or 'skip'.")

    def patch_vbmeta_image(self, vbmeta_path: Path) -> bool:
        """
        Patches an existing vbmeta.img binary header directly to disable or enable verity/verification.
        Returns True if modified, False otherwise.
        """
        if self.mode == "skip" or not vbmeta_path.exists():
            return False

        try:
            with open(vbmeta_path, "r+b") as f:
                data = f.read(256)
                if not data.startswith(AVB_MAGIC):
                    print(f"[AVB] Warning: {vbmeta_path.name} is not a valid AVB 2.0 image (missing AVB0 magic).")
                    return False

                # Read current flags uint32 at offset 120
                flags = struct.unpack(">I", data[120:124])[0]
                print(f"[AVB] Original vbmeta flags: 0x{flags:08x}")

                if self.mode == "disable":
                    new_flags = flags | AVB_FLAG_DISABLE_VERITY | AVB_FLAG_DISABLE_VERIFICATION
                    f.seek(120)
                    f.write(struct.pack(">I", new_flags))
                    print(f"[AVB] Patched vbmeta flags -> 0x{new_flags:08x} (Verity & Verification Disabled)")
                    return True
                elif self.mode == "enable":
                    new_flags = flags & ~(AVB_FLAG_DISABLE_VERITY | AVB_FLAG_DISABLE_VERIFICATION)
                    f.seek(120)
                    f.write(struct.pack(">I", new_flags))
                    print(f"[AVB] Patched vbmeta flags -> 0x{new_flags:08x} (Verity & Verification Enabled)")
                    return True
        except Exception as e:
            print(f"[AVB] Error patching vbmeta.img: {e}")
            return False

        return False

    def generate_recovery_script_snippet(self) -> str:
        """
        Generates the on-device shell script routine to be embedded directly into update-binary.
        Executes avbctl seamlessly during recovery installation without any external zip.
        """
        if self.mode == "skip":
            return """# AVB 2.0 / Vbmeta State: Skipped
ui_print "- Skipping AVB / Vbmeta modification (kept as-is)"
"""

        if self.mode == "disable":
            return """# AVB 2.0 / Vbmeta Control: DISABLE
ui_print "- Configuring AVB 2.0 (Vbmeta)..."
AVB_BIN="/system/bin/avbctl"
if [ ! -f "$AVB_BIN" ]; then
    if [ -f "/sbin/avbctl" ]; then
        AVB_BIN="/sbin/avbctl"
    else
        unzip -o "$ZIPFILE" "META-INF/bin/avbctl" -d /tmp >/dev/null 2>&1
        chmod 0755 /tmp/META-INF/bin/avbctl 2>/dev/null
        AVB_BIN="/tmp/META-INF/bin/avbctl"
    fi
fi

if [ -f "$AVB_BIN" ]; then
    VERITY_STAT=$($AVB_BIN get-verity 2>/dev/null || echo "unknown")
    if echo "$VERITY_STAT" | grep -qi "disabled"; then
        ui_print "  • AVB Status : Already Disabled [dm-verity OFF]"
    else
        $AVB_BIN --force disable-verity >/dev/null 2>&1 || true
        $AVB_BIN --force disable-verification >/dev/null 2>&1 || true
        ui_print "  • AVB Status : Disabled [dm-verity & verification OFF]"
    fi
else
    ui_print "  • AVB Status : Preserved (avbctl not in recovery)"
fi
"""

        if self.mode == "enable":
            return """# AVB 2.0 / Vbmeta Control: ENABLE
ui_print "- Configuring AVB 2.0 (Vbmeta)..."
AVB_BIN="/system/bin/avbctl"
if [ ! -f "$AVB_BIN" ]; then
    if [ -f "/sbin/avbctl" ]; then
        AVB_BIN="/sbin/avbctl"
    else
        unzip -o "$ZIPFILE" "META-INF/bin/avbctl" -d /tmp >/dev/null 2>&1
        chmod 0755 /tmp/META-INF/bin/avbctl 2>/dev/null
        AVB_BIN="/tmp/META-INF/bin/avbctl"
    fi
fi

if [ -f "$AVB_BIN" ]; then
    $AVB_BIN --force enable-verity >/dev/null 2>&1 || true
    $AVB_BIN --force enable-verification >/dev/null 2>&1 || true
    ui_print "  • AVB Status : Enabled [Strict Verification ON]"
fi
"""
        return ""
