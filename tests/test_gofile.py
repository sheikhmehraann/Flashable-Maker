import os
import sys
import json
import re
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gofile_transfer.uploader import GoFileUploader

def test_uploader():
    print("[*] Running GoFile uploader self-test...")
    test_file = "temp_test_payload.bin"
    with open(test_file, "wb") as f:
        f.write(b"0" * 1024)

    try:
        uploader = GoFileUploader()
        res = uploader.upload(test_file)
        print(f"[+] GoFile Upload Success: {res.download_page}")
        return True
    except Exception as e:
        print(f"[!] GoFile Upload Error: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    success = test_uploader()
    if not success:
        sys.exit(1)
