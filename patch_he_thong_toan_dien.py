# -*- coding: utf-8 -*-
"""
PATCH HE THONG TOAN DIEN - Tim va thay the chuoi version/IP cu
Chay: python patch_he_thong_toan_dien.py
"""

import os
import sys
import re
import zipfile
import io
import shutil
from pathlib import Path

# === CAU HINH ===
APP_PATH = r"d:\FileD\dota\ios\Payload\dgame.app"
DATA_PATH = os.path.join(APP_PATH, "data")

# Chuoi can thay the
OLD_IP = b"192.168.1.179"
NEW_IP = b"192.168.2.111"
OLD_VER = b"9.9.0"
NEW_VER = b"1.0.0"  # Giu do dai 5 byte nhu 9.9.0

# Danh sach file da xu ly
files_patched = []
files_error = []


def log(msg):
    print(f"  [PATCH] {msg}")


def patch_binary_file(filepath):
    """Doc file nhi phan, tim va thay the chuoi, ghi lai."""
    global files_patched, files_error
    
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        original_size = len(content)
        modified = False
        new_content = content
        
        # Thay the IP
        if OLD_IP in new_content:
            new_content = new_content.replace(OLD_IP, NEW_IP)
            log(f"  IP: {OLD_IP.decode()} -> {NEW_IP.decode()} | {filepath}")
            modified = True
        
        # Thay the version (tim chinh xac chuoi 9.9.0)
        if OLD_VER in new_content:
            # Dem so lan xuat hien
            count = new_content.count(OLD_VER)
            new_content = new_content.replace(OLD_VER, NEW_VER)
            log(f"  Version: {OLD_VER.decode()} -> {NEW_VER.decode()} (x{count}) | {filepath}")
            modified = True
        
        if modified:
            with open(filepath, 'wb') as f:
                f.write(new_content)
            files_patched.append(filepath)
            return True
            
    except Exception as e:
        files_error.append((filepath, str(e)))
        log(f"  LOI: {e} | {filepath}")
        return False
    
    return False


def patch_zip_file(filepath):
    """Xu ly file ZIP (.abc), thay the noi dung, giu nguyen kich thuoc."""
    global files_patched, files_error
    
    try:
        # Doc file goc
        with open(filepath, 'rb') as f:
            original_data = f.read()
        
        original_size = len(original_data)
        
        # Mo ZIP
        zin = zipfile.ZipFile(io.BytesIO(original_data), 'r')
        
        # Doc tat ca file trong ZIP
        file_contents = {}
        for name in zin.namelist():
            try:
                file_contents[name] = zin.read(name)
            except:
                file_contents[name] = b""
        zin.close()
        
        modified = False
        
        # Kiem tra va thay the trong noi dung
        for name in list(file_contents.keys()):
            content = file_contents[name]
            
            # Thay IP
            if OLD_IP in content:
                file_contents[name] = content.replace(OLD_IP, NEW_IP)
                log(f"  ZIP/{name}: IP patched")
                modified = True
            
            # Thay version
            if OLD_VER in content:
                file_contents[name] = file_contents[name].replace(OLD_VER, NEW_VER)
                log(f"  ZIP/{name}: Version patched")
                modified = True
        
        if not modified:
            return False
        
        # Tao ZIP moi
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, content in file_contents.items():
                zout.writestr(name, content)
        
        new_data = output.getvalue()
        new_size = len(new_data)
        
        # Neu kich thuoc khac, can bo sung byte de giu nguyen
        if new_size != original_size:
            delta = original_size - new_size
            if delta > 0:
                # Them null bytes vao cuoi
                new_data = new_data + b'\x00' * delta
                log(f"  Padding {delta} bytes de giu nguyen kich thuoc")
            elif delta < 0:
                log(f"  CANH BAO: File moi lon hon {abs(delta)} bytes!")
        
        # Ghi file
        with open(filepath, 'wb') as f:
            f.write(new_data[:original_size])  # Chi ghi dung kich thuoc goc
        
        files_patched.append(filepath)
        log(f"  ZIP da dong goi: {filepath}")
        return True
        
    except zipfile.BadZipFile:
        # Khong phai ZIP, thu patch nhu binary binh thuong
        return patch_binary_file(filepath)
    except Exception as e:
        files_error.append((filepath, str(e)))
        log(f"  LOI ZIP: {e} | {filepath}")
        return False


def scan_directory(dirpath, extensions=None):
    """Quet tat ca file trong thu muc."""
    results = []
    for root, dirs, files in os.walk(dirpath):
        for filename in files:
            filepath = os.path.join(root, filename)
            if extensions is None:
                results.append(filepath)
            else:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    results.append(filepath)
    return results


def main():
    global files_patched, files_error
    
    print("=" * 70)
    print("PATCH HE THONG TOAN DIEN - Version & IP Patcher")
    print("=" * 70)
    
    # === BUOC 1: Quet thu muc data ===
    print("\n[1] QUET THU MUC DATA...")
    if os.path.exists(DATA_PATH):
        data_files = scan_directory(DATA_PATH)
        print(f"  Tim thay {len(data_files)} file trong data/")
        
        for filepath in data_files:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.abc':
                patch_zip_file(filepath)
            else:
                patch_binary_file(filepath)
    else:
        print(f"  Khong tim thay: {DATA_PATH}")
    
    # === BUOC 2: Quet tat ca .dylib ===
    print("\n[2] QUET DYLIB TRONG dgame.app...")
    dylib_files = scan_directory(APP_PATH, {'.dylib'})
    print(f"  Tim thay {len(dylib_files)} file .dylib")
    
    for filepath in dylib_files:
        patch_binary_file(filepath)
    
    # === BUOC 3: Quet binary chinh ===
    print("\n[3] QUET BINARY CHINH...")
    main_binary = os.path.join(APP_PATH, "dgame")
    if os.path.exists(main_binary):
        patch_binary_file(main_binary)
        files_patched.append(main_binary)
    else:
        # Thu ten khac
        for name in ['dgame', 'dgame.app', 'DoTa Truyen Ky']:
            alt_path = os.path.join(APP_PATH, name)
            if os.path.exists(alt_path):
                patch_binary_file(alt_path)
                files_patched.append(alt_path)
                break
    
    # === BUOC 4: Kiem tra Info.plist ===
    print("\n[4] Kiem tra Info.plist...")
    info_plist = os.path.join(APP_PATH, "Info.plist")
    if os.path.exists(info_plist):
        with open(info_plist, 'rb') as f:
            content = f.read()
        
        if b'9.9.0' in content:
            content = content.replace(b'9.9.0', b'1.0.0')
            with open(info_plist, 'wb') as f:
                f.write(content)
            log(f"  Info.plist: Version patched")
            files_patched.append(info_plist)
        else:
            print("  Info.plist: Khong can sua")
    else:
        print("  Info.plist: Khong tim thay")
    
    # === BUOC 5: Quet cac file quan trong khac ===
    print("\n[5] QUET CAC FILE QUAN TRONG KHAC...")
    important_paths = [
        APP_PATH,
        os.path.join(APP_PATH, "Frameworks"),
        os.path.join(APP_PATH, "PlugIns"),
    ]
    
    for base_path in important_paths:
        if os.path.exists(base_path):
            all_files = scan_directory(base_path)
            for filepath in all_files:
                ext = os.path.splitext(filepath)[1].lower()
                # Chi xu ly cac file co the chua chuoi
                if ext in ['.plist', '.json', '.txt', '.xml', '.conf', '.config', '.lua', '.luac']:
                    patch_binary_file(filepath)
    
    # === KET QUA ===
    print("\n" + "=" * 70)
    print("KET QUA:")
    print("=" * 70)
    print(f"\n  Da patch thanh cong: {len(files_patched)} file")
    for f in files_patched:
        rel_path = f.replace(APP_PATH + "\\", "").replace(APP_PATH + "/", "")
        print(f"    + {rel_path}")
    
    if files_error:
        print(f"\n  Loi: {len(files_error)} file")
        for f, err in files_error:
            print(f"    ! {f}: {err}")
    
    print("\n" + "=" * 70)
    print("PATCH HOAN TAT!")
    print("=" * 70)


if __name__ == "__main__":
    main()
