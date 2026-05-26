# -*- coding: utf-8 -*-
"""
APK COMPREHENSIVE VALIDATION SCRIPT
Checks all components for potential black screen issues
"""

import os
import re
import zipfile
import io

def descramble_abc(encrypted, name):
    size = len(encrypted)
    buffer = bytearray(size)
    key = f'{name}.abc'.encode('utf-8')
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)

def validate_apk():
    print("=" * 70)
    print("APK COMPREHENSIVE VALIDATION")
    print("=" * 70)
    
    apk_base = r'd:\FileD\dota\apk\base'
    assets_dir = os.path.join(apk_base, 'assets')
    
    issues = []
    warnings = []
    passed = []
    
    # ========== 1. Check xggameinfo.txt ==========
    print("\n[1] Checking xggameinfo.txt (Server Config)...")
    xggameinfo = os.path.join(assets_dir, 'xggameinfo.txt')
    if os.path.exists(xggameinfo):
        with open(xggameinfo, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract IP/Port
        match = re.search(r'gameurl["\s:]+([^"]+)', content)
        if match:
            url = match.group(1)
            print(f"    Server URL: {url}")
            passed.append("xggameinfo.txt exists and has server config")
            
            # Check if IP format is valid
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', url)
            if ip_match:
                ip = ip_match.group(1)
                port = ip_match.group(2)
                print(f"    IP: {ip}")
                print(f"    Port: {port}")
                
                # Validate IP octets
                octets = ip.split('.')
                valid_ip = True
                for octet in octets:
                    val = int(octet)
                    if val < 0 or val > 255:
                        valid_ip = False
                        issues.append(f"Invalid IP octet: {ip}")
                
                if valid_ip:
                    passed.append("IP format is valid")
        else:
            issues.append("Cannot find gameurl in xggameinfo.txt")
    else:
        issues.append("xggameinfo.txt is MISSING!")
    
    # ========== 2. Check essential assets ==========
    print("\n[2] Checking Essential Assets...")
    
    essential_assets = [
        ('data/config.abc', 'Game config'),
        ('data/configloader.abc', 'Config loader'),
        ('data/gametable/common.abc', 'Common game table'),
        ('data/battle/battle_engine.abc', 'Battle engine'),
    ]
    
    for rel_path, desc in essential_assets:
        full_path = os.path.join(assets_dir, rel_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            if size > 0:
                passed.append(f"{desc}: OK ({size} bytes)")
            else:
                issues.append(f"{desc}: EMPTY FILE!")
        else:
            issues.append(f"{desc}: MISSING ({rel_path})")
    
    # ========== 3. Check data folders ==========
    print("\n[3] Checking Data Folders...")
    
    required_folders = [
        'data/battle',
        'data/bot',
        'data/player',
        'data/json',
        'data/gametable',
    ]
    
    for folder in required_folders:
        full_path = os.path.join(assets_dir, folder)
        if os.path.exists(full_path):
            count = len(os.listdir(full_path))
            if count > 0:
                passed.append(f"data/{folder.split('/')[-1]}: {count} files")
            else:
                warnings.append(f"data/{folder.split('/')[-1]}: EMPTY!")
        else:
            issues.append(f"data/{folder.split('/')[-1]}: MISSING!")
    
    # ========== 4. Check Native Libraries ==========
    print("\n[4] Checking Native Libraries...")
    
    lib_dir = os.path.join(apk_base, 'lib')
    if os.path.exists(lib_dir):
        archs = os.listdir(lib_dir)
        print(f"    Architectures: {archs}")
        
        required_libs = ['libhellolua.so', 'libmchpaysdk.so', 
                       'libemulator_check.so', 'libproperty_get.so']
        
        for arch in archs:
            arch_path = os.path.join(lib_dir, arch)
            for lib in required_libs:
                lib_path = os.path.join(arch_path, lib)
                if os.path.exists(lib_path):
                    size = os.path.getsize(lib_path)
                    if size > 1000:
                        passed.append(f"{arch}/{lib}: {size} bytes")
                    else:
                        warnings.append(f"{arch}/{lib}: Suspicious small size ({size} bytes)")
                else:
                    issues.append(f"{arch}/{lib}: MISSING!")
    else:
        issues.append("lib/ directory: MISSING!")
    
    # ========== 5. Check Core APK Files ==========
    print("\n[5] Checking Core APK Files...")
    
    core_files = {
        'AndroidManifest.xml': 1000,
        'classes.dex': 100000,
        'resources.arsc': 1000,
    }
    
    for file, min_size in core_files.items():
        full_path = os.path.join(apk_base, file)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            if size >= min_size:
                passed.append(f"{file}: {size} bytes")
            else:
                issues.append(f"{file}: Too small ({size} bytes)")
        else:
            issues.append(f"{file}: MISSING!")
    
    # ========== 6. Check META-INF ==========
    print("\n[6] Checking META-INF Signatures...")
    
    meta_dir = os.path.join(apk_base, 'META-INF')
    if os.path.exists(meta_dir):
        sig_files = os.listdir(meta_dir)
        print(f"    Signature files: {sig_files}")
        passed.append("META-INF signatures present")
    else:
        warnings.append("META-INF: NOT FOUND (unsigned build - may not install on some devices)")
    
    # ========== 7. Check Icons ==========
    print("\n[7] Checking Icons...")
    
    icons_dir = r'd:\FileD\dota\apk\icons'
    if os.path.exists(icons_dir):
        count = len(os.listdir(icons_dir))
        if count > 0:
            passed.append(f"Icons: {count} files")
        else:
            warnings.append("Icons folder is EMPTY")
    else:
        warnings.append("Icons folder: MISSING")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\n[PASSED] {len(passed)} items")
    for p in passed[:10]:
        print(f"    [P] {p}")
    if len(passed) > 10:
        print(f"    ... and {len(passed)-10} more")
    
    if warnings:
        print(f"\n[WARNINGS] {len(warnings)} items")
        for w in warnings:
            print(f"    [W] {w}")
    
    if issues:
        print(f"\n[ISSUES] {len(issues)} items")
        for i in issues:
            print(f"    [X] {i}")
    else:
        print("\n✗ ISSUES: None")
    
    # Final verdict
    print("\n" + "=" * 70)
    if issues:
        print("RESULT: APK HAS ISSUES - MAY CAUSE BLACK SCREEN")
        return False
    elif warnings:
        print("RESULT: APK HAS WARNINGS - PROCEED WITH CAUTION")
        return True
    else:
        print("RESULT: APK STRUCTURE IS VALID")
        return True

if __name__ == "__main__":
    validate_apk()
