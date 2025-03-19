import subprocess
import tempfile
import hashlib
import base64
import shutil
import glob
import sys
import os
import re

JADX_PATH = shutil.which('jadx')
if not JADX_PATH:
    print("Error: 'jadx' is not installed or not found in your PATH.")
    print("Please install jadx from https://github.com/skylot/jadx before running this script.")
    sys.exit(1)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_pattern(line, pattern):
    match = re.search(pattern, line)
    return match.group(1) if match else None

def extract_ips_from_apk(apk_path):
    md5_hash = calculate_md5(apk_path)
    print(f"Processing {apk_path}")
    print(f"[*] Decompiling APK: [{md5_hash}]")
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run([JADX_PATH, '--no-res', '-d', temp_dir, apk_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("[*] Finding the C2 IP Address...")
        java_files = glob.glob(os.path.join(temp_dir, '**', '*.java'), recursive=True)
        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    if (value := find_pattern(line, r'public static String ClientHost\s*=\s*"([^"]+)"')):
                        decode(value, "IP Address")
                    elif (value := find_pattern(line, r'public static String ClientPort\s*=\s*"([^"]+)"')):
                        decode(value, "Port")
                    elif (value := find_pattern(line, r'public static String ConnectionKey\s*=\s*"([^"]+)"')):
                        decode(value, "Connection Key")
        print()

def decode(value, key_type):
    try:
        padded_value = value + '=' * (-len(value) % 4)
        decoded_value = base64.b64decode(padded_value).decode('utf-8', errors='ignore')
        print(f"{key_type}: {decoded_value}")
    except Exception as e:
        print(f"Error decoding {key_type}: {value} - {e}")

def main():
    if len(sys.argv) != 2:
        print('Usage: python craxsrat_ip_extractor.py /path/to/apk/folder')
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print('Invalid directory path')
        sys.exit(1)

    # Collect all files in the folder
    files = glob.glob(os.path.join(folder_path, '**', '*.apk'), recursive=True)
    if not files:
        print(f"No APK file found in {folder_path}")
        sys.exit(1)

    print(f"[*] Found {len(files)} APK file(s) in {folder_path}\n")

    for file_path in files:
        extract_ips_from_apk(file_path)

if __name__ == '__main__':
    main()
