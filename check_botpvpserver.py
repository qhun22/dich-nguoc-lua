# -*- coding: utf-8 -*-
"""Kiem tra noi dung botpvpserver.luac"""
import os

path = r'd:\FileD\dota\ios\dgame.app\data\bot\botpvpserver.luac'

with open(path, 'rb') as f:
    data = f.read()

print(f'Kich thuoc: {len(data)} bytes')
print(f'Tim thay 192.168.1.179: {b"192.168.1.179" in data}')
print(f'Tim thay 9.9.0: {b"9.9.0" in data}')
print(f'Tim thay 192.168.2.111: {b"192.168.2.111" in data}')
print(f'Tim thay 1.0.0103: {b"1.0.0103" in data}')

# Tim vi tri
for search in [b'192.168.1.179', b'9.9.0', b'192.168.2.111', b'1.0.0103']:
    idx = data.find(search)
    if idx >= 0:
        print(f'\nTim thay "{search.decode()}":')
        print(f'  Vi tri: {idx}')
        start = max(0, idx - 30)
        end = min(len(data), idx + len(search) + 30)
        print(f'  Context hex: {data[start:end].hex()}')
        try:
            print(f'  Context text: {data[start:end].decode("utf-8", errors="replace")}')
        except:
            pass
