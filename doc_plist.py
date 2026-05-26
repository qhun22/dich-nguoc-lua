# -*- coding: utf-8 -*-
"""Doc noi dung xggameinfo.plist"""
import sys

path = r'd:\FileD\dota\ios\dgame.app\xggameinfo.plist'

with open(path, 'rb') as f:
    data = f.read()

# Tim versionStr
idx = data.find(b'versionStr')
if idx >= 0:
    print(f"Tim thay 'versionStr' tai vi tri {idx}")
    # Hien thi context
    start = max(0, idx - 100)
    end = min(len(data), idx + 200)
    print(f"\nContext (hex):")
    print(data[start:end].hex())
    print(f"\nContext (text):")
    try:
        print(data[start:end].decode('utf-16', errors='replace'))
    except:
        print(data[start:end].decode('latin-1', errors='replace'))

# Hien thi toan bo noi dung
print(f"\n\nToan bo noi dung ({len(data)} bytes):")
print(data.decode('utf-16-le', errors='replace')[:2000])
