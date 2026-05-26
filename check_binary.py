# -*- coding: utf-8 -*-
"""Kiem tra version trong binary dgame"""
import os

path = r'd:\FileD\dota\ios\dgame.app\dgame'

with open(path, 'rb') as f:
    data = f.read()

print(f"Kich thuoc binary: {len(data)} bytes")

# Tim cac vi tri chua 9.9.0
search = b'9.9.0'
pos = 0
count = 0
while True:
    pos = data.find(search, pos)
    if pos == -1 or count > 10:
        break
    print(f"\nTim thay '9.9.0' tai vi tri: {pos}")
    # Hien thi context
    start = max(0, pos - 50)
    end = min(len(data), pos + 100)
    print(f"  Hex: {data[start:end].hex()[:200]}")
    try:
        print(f"  Text: {data[start:end].decode('utf-8', errors='replace')[:100]}")
    except:
        pass
    count += 1
    pos += 1

print(f"\n\nTong so lan xuat hien '9.9.0': {data.count(search)}")

# Tim versionStr
print("\n" + "="*50)
print("TIM KIEM versionStr:")
search2 = b'versionStr'
pos = 0
count = 0
while True:
    pos = data.find(search2, pos)
    if pos == -1 or count > 5:
        break
    print(f"\nTim thay 'versionStr' tai vi tri: {pos}")
    start = max(0, pos - 20)
    end = min(len(data), pos + 50)
    print(f"  Hex: {data[start:end].hex()[:150]}")
    count += 1
    pos += 1
