import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

zip_path = r'C:\Users\Admin\Downloads\logs_86048241532.zip'
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        print(f"=== File: {name} ===")
        try:
            content = z.read(name).decode('utf-8', errors='replace')
            print(content[:3000])
        except Exception as e:
            print("Error reading:", e)
        print("="*40)
