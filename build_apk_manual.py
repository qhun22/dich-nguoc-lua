# -*- coding: utf-8 -*-
"""
APK Manual Build Script
Zips the APK folder structure into a valid APK
"""

import os
import zipfile

APK_DIR = r"d:\FileD\dota\apk\base"
OUTPUT_APK = r"d:\FileD\dota\game.apk"

def build_apk():
    print("=" * 60)
    print("APK BUILD (Manual Zip)")
    print("=" * 60)
    
    if os.path.exists(OUTPUT_APK):
        os.remove(OUTPUT_APK)
        print("Removed old APK")
    
    print(f"\nBuilding APK from: {APK_DIR}")
    
    # Collect all files
    files_to_add = []
    total_size = 0
    for root, dirs, files in os.walk(APK_DIR):
        for f in files:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            arcname = os.path.relpath(path, APK_DIR)
            files_to_add.append((path, arcname, size))
            total_size += size
    
    print(f"Found {len(files_to_add)} files")
    print(f"Total size: {total_size/1024/1024:.2f} MB")
    
    # Create ZIP (APK is just a ZIP)
    print("\nCreating APK...")
    with zipfile.ZipFile(OUTPUT_APK, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path, arcname, size in files_to_add:
            zf.write(path, arcname)
            print(f"  Added: {arcname}")
    
    apk_size = os.path.getsize(OUTPUT_APK)
    print(f"\nAPK created: {OUTPUT_APK}")
    print(f"APK size: {apk_size/1024/1024:.2f} MB")
    print("\nNOTE: This APK is unsigned. Use 'apksigner' to sign before installing.")

if __name__ == "__main__":
    build_apk()
