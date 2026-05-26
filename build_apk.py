# -*- coding: utf-8 -*-
"""
APK BUILD SCRIPT - Complete APK Packaging
Requires: apktool (https://apktool.org/)
"""

import os
import sys
import subprocess
import shutil

# === CONFIGURATION ===
APK_DIR = r"d:\FileD\dota\apk"
OUTPUT_APK = r"d:\FileD\dota\game_android.apk"

def print_header():
    print("=" * 60)
    print("APK BUILD SCRIPT")
    print("=" * 60)

def check_apktool():
    """Check if apktool is installed."""
    print("\n[CHECK] Verifying apktool installation...")
    try:
        result = subprocess.run(["apktool.bat", "-version"], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"  apktool: {result.stdout.strip()} OK")
            return True
    except FileNotFoundError:
        pass
    
    print("  ERROR: apktool not found!")
    print("  Please install apktool:")
    print("  1. Download apktool.jar from https://apktool.org/")
    print("  2. Save to C:\\Windows\\apktool.jar")
    print("  3. Create apktool.bat in same folder:")
    print("     @echo off")
    print("     java -jar \"%~dp0apktool.jar\" %*")
    return False

def verify_structure():
    """Verify APK structure before building."""
    print("\n[CHECK] Verifying APK structure...")
    
    base_dir = os.path.join(APK_DIR, "base")
    issues = []
    
    # Essential files
    essential = {
        "AndroidManifest.xml": "Manifest",
        "classes.dex": "DEX Code",
        "resources.arsc": "Resources",
    }
    
    for file, name in essential.items():
        path = os.path.join(base_dir, file)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  {file}: {size:,} bytes OK")
        else:
            issues.append(f"MISSING: {file} ({name})")
    
    # Native libraries
    lib_dir = os.path.join(base_dir, "lib")
    if os.path.exists(lib_dir):
        arch_count = len(os.listdir(lib_dir))
        print(f"  lib/: {arch_count} architectures OK")
    else:
        issues.append("MISSING: lib/ directory")
    
    # Assets
    assets_dir = os.path.join(base_dir, "assets")
    if os.path.exists(assets_dir):
        print(f"  assets/: OK")
        # Check xggameinfo
        xggameinfo = os.path.join(assets_dir, "xggameinfo.txt")
        if os.path.exists(xggameinfo):
            print(f"  xggameinfo.txt: OK")
        else:
            issues.append("MISSING: xggameinfo.txt")
    else:
        issues.append("MISSING: assets/ directory")
    
    if issues:
        print("\n  ISSUES FOUND:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    
    print("\n  Structure: ALL OK")
    return True

def build_apk():
    """Build the APK using apktool."""
    print("\n[BUILD] Building APK...")
    
    # Remove old output if exists
    if os.path.exists(OUTPUT_APK):
        os.remove(OUTPUT_APK)
        print("  Removed old APK")
    
    # Build command
    cmd = ["apktool.bat", "b", APK_DIR, "-o", OUTPUT_APK]
    
    print(f"  Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  APK built successfully: {OUTPUT_APK}")
            size = os.path.getsize(OUTPUT_APK)
            print(f"  Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
            return True
        else:
            print(f"  Build failed!")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print_header()
    
    if not check_apktool():
        sys.exit(1)
    
    if not verify_structure():
        print("\nERROR: Cannot build APK due to missing files")
        sys.exit(1)
    
    if build_apk():
        print("\n" + "=" * 60)
        print("BUILD COMPLETE!")
        print("=" * 60)
        print(f"Output: {OUTPUT_APK}")
    else:
        print("\nBUILD FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
