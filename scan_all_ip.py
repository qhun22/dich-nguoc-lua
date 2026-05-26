# -*- coding: utf-8 -*-
import zipfile
import io
import os
import re
import glob

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

def check_file(filepath):
    name = os.path.basename(filepath).replace('.abc', '')
    try:
        with open(filepath, 'rb') as f:
            abc_data = f.read()
        
        zip_data = descramble_abc(abc_data, name)
        pwd = f'cocos2d: ERROR: Invalid filename {name}'.encode('utf-8')
        
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            lua_data = zf.read('data', pwd=pwd)
            
        # Extract strings
        strings = re.findall(b'[\x20-\x7e]{6,}', lua_data)
        
        found = []
        for s in strings:
            s_str = s.decode('utf-8', errors='replace')
            # IP patterns
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', s_str):
                found.append(('IP', s_str))
            # URL patterns
            elif 'http://' in s_str.lower() or 'https://' in s_str.lower():
                found.append(('URL', s_str))
        
        if found:
            return found
        return None
    except Exception as e:
        return None

# Scan all abc files in data folder
data_dir = r'd:\FileD\dota\apk\base\assets\data'
abc_files = glob.glob(f'{data_dir}/**/*.abc', recursive=True)

print("=" * 60)
print("SCANNING ALL ABC FILES FOR IP/SERVER REFERENCES")
print("=" * 60)

results = {}
for filepath in abc_files:
    rel_path = os.path.relpath(filepath, data_dir)
    found = check_file(filepath)
    if found:
        results[rel_path] = found

if results:
    print(f"\nFOUND {len(results)} FILES WITH IP/URL:\n")
    for filepath, items in sorted(results.items()):
        print(f"[{filepath}]")
        for item_type, value in items:
            print(f"  {item_type}: {value}")
        print()
else:
    print("\nNo IP/URL found in any abc files")

print("\n" + "=" * 60)
print("FILES LIST (total abc files)")
print("=" * 60)
for f in sorted(abc_files):
    rel_path = os.path.relpath(f, data_dir)
    print(f"  {rel_path}")
