# -*- coding: utf-8 -*-
"""Kiem tra noi dung cac file .luac"""
import os

def kiem_tra_file(path):
    print(f"\n{'='*60}")
    print(f"File: {path}")
    print('='*60)
    
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"Kich thuoc: {len(data)} bytes")
    
    # Cac chuoi can tim
    search_strings = [
        b"192.168.1.179",
        b"192.168.2.2",
        b"192.168.2.111",
        b"9.9.0",
        b"1.0.0103",
        b"versionStr",
    ]
    
    for s in search_strings:
        if s in data:
            print(f"  [TIM THAY] {s.decode('utf-8', errors='replace')}")
            # Hien thi vi tri
            idx = 0
            while True:
                idx = data.find(s, idx)
                if idx == -1:
                    break
                print(f"    -> Vi tri: {idx}")
                # Hien thi context
                start = max(0, idx - 20)
                end = min(len(data), idx + len(s) + 20)
                context = data[start:end].decode('utf-8', errors='replace')
                print(f"       Context: ...{context}...")
                idx += len(s)
    
    # Hien thi tat ca cac chuoi co trong file
    print("\n[Cac dong chua IP hoac version:]")
    try:
        text = data.decode('utf-8', errors='replace')
        for line in text.split('\n'):
            line_lower = line.lower()
            if '192' in line or 'version' in line_lower or '9.9' in line or '1.0.0' in line:
                print(f"  {line[:150]}")
    except Exception as e:
        print(f"  Loi decode: {e}")

# Kiem tra cac file luac
luac_files = [
    r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac",
    r"d:\FileD\dota\ios\dgame.app\data\bot\botpvpserver.luac",
]

for f in luac_files:
    if os.path.exists(f):
        kiem_tra_file(f)
    else:
        print(f"[LOI] Khong ton tai: {f}")
