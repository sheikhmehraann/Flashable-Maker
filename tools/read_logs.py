import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

zip_path = r'C:\Users\Admin\Downloads\logs_86048241532.zip'
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            print(f"=== File: {name} ===")
            try:
                content = z.read(name).decode('utf-8', errors='replace')
                print(content[:3000])
            except Exception as e:
                print("Error reading:", e)
            print("="*40)
else:
    print(f"Log zip file not found: {zip_path}")
